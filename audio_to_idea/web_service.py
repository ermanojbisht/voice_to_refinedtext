"""Web backend service for Audio to Ideas.

Provides a thread-safe state container and controller for batch audio processing,
transcript editing, prompt management, and live SSE event broadcasting.
"""
from copy import deepcopy
import json
import mimetypes
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import time
from typing import Dict, Any, List, Optional, Tuple

from .audio import EXTENSIONS
from .config import ROOT, load_settings, update_settings
from .jobs import JobService, destination, inputs, save_transcript_edit
from .models import doctor
from .profiles import load_profile
from .storage import atomic_write, fingerprint, read_json
from .templates import BUILTINS, MODES, Template, load_template, validate_template
from .watcher import Watcher


class AudioIdeaWebService:
    """Singleton service managing Audio-to-Ideas state, jobs, and SSE broadcasting."""
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "AudioIdeaWebService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self.settings = load_settings()
        self.items: List[Dict[str, Any]] = []
        self.items_lock = threading.Lock()
        self.selected_id: Optional[str] = None
        self.worker: Optional[threading.Thread] = None
        self.cancel = threading.Event()
        self.status_message = "Ready. Add recordings to begin."
        self.progress_value = 0.0
        self.progress_stage = "idle"
        
        # SSE broadcasting
        self.subscribers: List[queue.Queue] = []
        self.subscribers_lock = threading.Lock()

        # Watcher
        self.watcher: Optional[Watcher] = None
        self.watcher_worker: Optional[threading.Thread] = None
        self.watcher_cancel = threading.Event()
        self.watcher_folder: Optional[str] = None

    def reload_settings(self):
        self.settings = load_settings()
        return self.settings

    def update_audio_settings(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        update_settings(self.settings.path, patch)
        self.reload_settings()
        self.broadcast_event({"type": "settings_updated", "settings": self.settings.data})
        return {"ok": True, "settings": self.settings.data}

    def is_busy(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def is_watching(self) -> bool:
        return self.watcher_worker is not None and self.watcher_worker.is_alive()

    # --- SSE Event Broadcasting ---
    def subscribe_events(self) -> queue.Queue:
        q = queue.Queue(maxsize=100)
        with self.subscribers_lock:
            self.subscribers.append(q)
        return q

    def unsubscribe_events(self, q: queue.Queue):
        with self.subscribers_lock:
            if q in self.subscribers:
                self.subscribers.remove(q)

    def broadcast_event(self, event: Dict[str, Any]):
        with self.subscribers_lock:
            dead = []
            for q in self.subscribers:
                try:
                    q.put_nowait(event)
                except queue.Full:
                    dead.append(q)
            for q in dead:
                if q in self.subscribers:
                    self.subscribers.remove(q)

    # --- Queue Management ---
    def add_paths(self, paths: List[str], input_root: Optional[str] = None) -> List[Dict[str, Any]]:
        added = []
        with self.items_lock:
            for p in paths:
                try:
                    resolved = Path(p).expanduser().resolve()
                    if not resolved.exists():
                        continue
                    # Check if directory
                    if resolved.is_dir():
                        discovered = inputs(resolved)
                        for d in discovered:
                            self._add_single_item(d, resolved, added)
                    elif resolved.is_file() and resolved.suffix.lower() in EXTENSIONS:
                        self._add_single_item(resolved, input_root or resolved, added)
                except Exception as exc:
                    print(f"[web_service] Error adding path {p}: {exc}")
        if added:
            self.broadcast_event({"type": "items_added", "count": len(added)})
        return added

    def _add_single_item(self, source: Path, input_root: Any, added_list: List[Dict[str, Any]]):
        source = Path(source).resolve()
        input_root = Path(input_root).resolve() if input_root else source
        # Avoid duplicate source paths
        if any(i["source"] == str(source) for i in self.items):
            return
        item_id = fingerprint(str(source))[:12]
        output_dir = self.settings.data.get("output", {}).get("directory")
        if not output_dir:
            try:
                from storage_manager import get_audio_to_idea_output_dir
                output_dir = str(get_audio_to_idea_output_dir())
            except Exception:
                output_dir = None
        output, base_name = destination(source, input_root, output_dir)
        directory = Path(output or source.parent).resolve()
        directory.mkdir(parents=True, exist_ok=True)

        # Unique session stem: YYYYMMDD_HHMMSS_<stem>
        import datetime
        now_prefix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{now_prefix}_{base_name}"
        
        # Check if workspace already exists to restore prior results
        key = fingerprint(str(source))[:20]
        workspace = directory / ".audio2idea" / key
        manifest_path = workspace / "manifest.json"
        
        result = None
        status = "queued"
        if manifest_path.is_file():
            try:
                manifest = read_json(manifest_path)
                status = manifest.get("status", "complete")
                transcript_rel = manifest.get("edit", {}).get("filename") or manifest.get("transcript")
                transcript_path = str(workspace / transcript_rel) if transcript_rel else None
                candidate_suffixes = ["_idea.txt", "_clean.txt", "_summary.txt", "_english.txt", "_hindi.txt", "_bilingual.txt", "_hinglish.txt"]
                idea_file = next((p for s in candidate_suffixes for p in directory.glob(f"*{base_name}{s}")), None)
                result = {
                    "source": str(source),
                    "workspace": str(workspace),
                    "status": status,
                    "transcript_path": transcript_path,
                    "processed_path": str(idea_file) if idea_file else None,
                    "outputs": [str(p) for p in directory.glob(f"*{base_name}*")],
                    "acoustic_suggestion": manifest.get("acoustic_suggestion"),
                    "acoustic_info": manifest.get("acoustic_info"),
                }
            except Exception:
                pass

        item = {
            "id": item_id,
            "source": str(source),
            "filename": source.name,
            "input_root": str(input_root),
            "output": str(output),
            "name": name,
            "status": status,
            "result": result,
            "size_bytes": source.stat().st_size if source.exists() else 0,
        }
        self.items.append(item)
        added_list.append(item)
        if not self.selected_id:
            self.selected_id = item_id

    def remove_item(self, item_id: str) -> bool:
        with self.items_lock:
            original_len = len(self.items)
            self.items = [i for i in self.items if i["id"] != item_id]
            if self.selected_id == item_id:
                self.selected_id = self.items[0]["id"] if self.items else None
            changed = len(self.items) != original_len
        if changed:
            self.broadcast_event({"type": "item_removed", "id": item_id})
        return changed

    def clear_queue(self, completed_only: bool = False):
        with self.items_lock:
            if completed_only:
                self.items = [i for i in self.items if i["status"] != "complete"]
            else:
                self.items = []
            if not any(i["id"] == self.selected_id for i in self.items):
                self.selected_id = self.items[0]["id"] if self.items else None
        self.broadcast_event({"type": "queue_cleared"})

    # --- Item Detail & Transcript Loading ---
    def get_item_detail(self, item_id: str) -> Optional[Dict[str, Any]]:
        with self.items_lock:
            item = next((i for i in self.items if i["id"] == item_id), None)
            if not item:
                return None
            item = deepcopy(item)

        result = item.get("result") or {}
        detail = {
            "item": item,
            "segments": [],
            "raw_segments": [],
            "editable_text": "",
            "raw_text": "",
            "idea_text": "",
            "idea_rendered": "",
            "metadata": {},
            "audio_url": f"/api/audio_to_idea/audio_stream?path={urllib_quote(item['source'])}",
        }

        if result.get("transcript_path") and Path(result["transcript_path"]).exists():
            try:
                data = read_json(result["transcript_path"])
                segments = data.get("segments", [])
                detail["segments"] = segments
                detail["editable_text"] = "\n".join(f"[{s['id']}] {s['text']}" for s in segments)
                
                # Try loading raw ASR
                workspace = Path(result["workspace"])
                manifest_path = workspace / "manifest.json"
                if manifest_path.exists():
                    manifest = read_json(manifest_path)
                    raw_path = workspace / manifest.get("transcript", "")
                    if raw_path.exists():
                        raw_data = read_json(raw_path)
                        detail["raw_segments"] = raw_data.get("segments", [])
                        detail["raw_text"] = "\n".join(
                            f"[{s['id']} {s.get('start', 0.0):.2f}s] {s['text']}" for s in raw_data.get("segments", [])
                        )

                # Load processed idea text prioritized by current or processed synthesis mode
                mode = result.get("synthesis_mode") or self.settings.data["synthesis"].get("mode", "clean_bilingual")
                mode_suffixes = {
                    'clean_paragraph': '_clean.txt',
                    'clean_bilingual': '_bilingual.txt',
                    'official_english': '_english.txt',
                    'official_hindi': '_hindi.txt',
                    'roman_hinglish': '_hinglish.txt',
                    'concise_summary': '_summary.txt',
                    'ideas_actions': '_idea.txt'
                }
                preferred = mode_suffixes.get(mode)
                base_suffixes = ["_idea.txt", "_clean.txt", "_summary.txt", "_english.txt", "_hindi.txt", "_bilingual.txt", "_hinglish.txt"]
                candidate_suffixes = ([preferred] + [s for s in base_suffixes if s != preferred]) if preferred else base_suffixes

                idea_file = (
                    Path(result["processed_path"])
                    if result.get("processed_path")
                    else next((Path(p) for s in candidate_suffixes for p in result.get("outputs", []) if str(p).endswith(s)), None)
                )
                if not idea_file or not idea_file.exists():
                    directory = Path(item.get("output") or self.settings.data["output"]["directory"] or Path(item["source"]).parent).resolve()
                    name = item.get("name", Path(item["source"]).stem)
                    idea_file = next((p for s in candidate_suffixes for p in directory.glob(f"{name}{s}")), None)
                    if not idea_file or not idea_file.exists():
                        stem = Path(item["source"]).stem
                        idea_file = next((p for s in candidate_suffixes for p in directory.glob(f"*{stem}{s}")), None)

                if idea_file and idea_file.exists():
                    detail["idea_text"] = idea_file.read_text(encoding="utf-8")
                elif result.get("error"):
                    detail["idea_text"] = f"Processed text unavailable. Transcript is preserved.\n\n{result['error']}"
            except Exception as exc:
                detail["error"] = str(exc)

        if result.get("acoustic_suggestion"):
            detail["acoustic_suggestion"] = result["acoustic_suggestion"]
        if result.get("acoustic_info"):
            detail["acoustic_info"] = result["acoustic_info"]

        return detail

    # --- Transcript Revision Saving ---
    def save_transcript(self, item_id: str, text: str) -> Dict[str, Any]:
        if self.is_busy():
            raise ValueError("Wait for processing to finish before saving transcript revisions.")

        with self.items_lock:
            item = next((i for i in self.items if i["id"] == item_id), None)
            if not item:
                raise ValueError("Item not found.")
            result = item.get("result") or {}
            workspace = result.get("workspace")
            if not workspace or not Path(workspace).exists():
                raise ValueError("No transcript workspace exists for this recording yet.")

        # Parse segment IDs
        edits, current = {}, None
        for line in text.splitlines():
            match = re.match(r"^\[(S\d+)\]\s?(.*)$", line)
            if match:
                current = match[1]
                if current in edits:
                    raise ValueError(f"Duplicate segment ID: {current}")
                edits[current] = match[2]
            elif current:
                edits[current] += "\n" + line
            elif line.strip():
                raise ValueError("Keep segment IDs such as [S00001] at the start of each segment.")

        # Save revision atomically
        new_path = save_transcript_edit(workspace, edits)
        with self.items_lock:
            result["transcript_path"] = str(new_path)
            item["status"] = "edited"
            item["result"] = result

        self.broadcast_event({
            "type": "transcript_saved",
            "id": item_id,
            "status": "edited",
            "transcript_path": str(new_path),
        })
        return {"ok": True, "path": str(new_path), "status": "edited"}

    # --- Job Execution ---
    def start_processing(
        self,
        summary: bool = True,
        selected_only: bool = False,
        mode: Optional[str] = None,
        profile: Optional[str] = None,
        context: str = "",
        preset: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.is_busy():
            return {"ok": False, "error": "A job is already running."}

        with self.items_lock:
            if selected_only and self.selected_id:
                pending = [i for i in self.items if i["id"] == self.selected_id]
            else:
                pending = [i for i in self.items if i["status"] != "complete"]
                # If all items were previously completed, reset to pending so user can re-process with new goal
                if not pending and self.items:
                    for i in self.items:
                        i["status"] = "pending"
                    pending = list(self.items)

            if not pending:
                return {"ok": False, "error": "No recordings found to process."}

            targets = list(pending)

        # Update mode if explicitly requested
        cfg = deepcopy(self.settings.data)
        cfg["output"]["overwrite"] = True
        cfg["output"]["allow_overwrite"] = True

        # Synchronize ASR settings from active or requested ASR preset
        try:
            from refiner_service import RefinerService
            ref_svc = RefinerService.get_instance()
            active_preset_key = preset or ref_svc.engine.get_active_preset()
            presets = ref_svc.engine.config.get("ASR_PRESETS", {})
            if active_preset_key in presets:
                p = presets[active_preset_key]
                cfg["asr"]["active_profile"] = active_preset_key
                cfg["active_preset"] = active_preset_key
                backend_str = p.get("backend", "faster_whisper")
                cfg["asr"]["backend"] = backend_str
                if backend_str in ("faster_whisper", "faster-whisper"):
                    model_val = p.get("model", "large-v3-turbo")
                    if model_val in ("large-v3-turbo", "turbo"):
                        cfg["asr"]["model_id"] = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
                    else:
                        cfg["asr"]["model_id"] = model_val
                    cfg["asr"]["model_path"] = None
                else:
                    cfg["asr"]["model_path"] = p.get("model", "")
                    cfg["asr"]["model_id"] = p.get("model", "")
                if p.get("asr_language"):
                    cfg["asr"]["language"] = p["asr_language"]
                if p.get("device"):
                    cfg["asr"]["device"] = p["device"]
            else:
                cfg["active_preset"] = active_preset_key
                cfg["asr"]["active_profile"] = active_preset_key
        except Exception as e:
            print(f"[web_service] Warning syncing active ASR preset: {e}")

        if mode and mode in MODES:
            cfg["synthesis"]["mode"] = mode
            mode_lang_map = {
                'clean_bilingual': 'source',
                'official_english': 'English',
                'official_hindi': 'Devanagari Hindi',
                'roman_hinglish': 'Roman Hinglish',
                'clean_paragraph': 'source',
            }
            if mode in mode_lang_map:
                cfg["synthesis"]["output_language"] = mode_lang_map[mode]
            update_settings(self.settings.path, {"synthesis.mode": mode})
            self.settings.data["synthesis"]["mode"] = mode

        # Synchronize LLM Synthesis Model based on Goal
        try:
            from refiner_service import RefinerService
            ref_svc = RefinerService.get_instance()
            target_mode = mode or cfg["synthesis"].get("mode", "clean_bilingual")
            if target_mode in ("official_hindi", "pure_hindi"):
                hi_model = ref_svc.engine.config.get("OLLAMA_MODELS", {}).get("hi")
                if hi_model:
                    cfg["synthesis"]["model"] = hi_model
            elif target_mode in ("official_english", "clean_bilingual", "ideas_actions", "concise_summary", "roman_hinglish"):
                en_model = ref_svc.engine.config.get("OLLAMA_MODELS", {}).get("en")
                if en_model:
                    cfg["synthesis"]["model"] = en_model
        except Exception as e:
            print(f"[web_service] Warning syncing synthesis model: {e}")

        self.cancel.clear()
        self.progress_stage = "running"
        self.progress_value = 0.0

        def runner():
            try:
                service = JobService(cfg)
                if summary:
                    service.snapshot_prompt()

                total_items = len(targets)
                for idx, item in enumerate(targets):
                    if self.cancel.is_set():
                        break

                    source = Path(item["source"])
                    output = Path(item["output"])
                    name = item["name"]

                    self.broadcast_event({
                        "type": "job_progress",
                        "stage": "running",
                        "item_id": item["id"],
                        "message": f"Processing {source.name} ({idx+1}/{total_items})",
                        "current": idx,
                        "total": total_items,
                    })

                    def on_notify(evt):
                        # Relay internal progress events
                        evt_type = evt.get("stage", "progress")
                        self.broadcast_event({
                            "type": "job_event",
                            "item_id": item["id"],
                            "stage": evt_type,
                            "message": evt.get("message", ""),
                            "current": evt.get("current", 0),
                            "total": evt.get("total", 0),
                        })
                        if "result" in evt:
                            res = evt["result"]
                            with self.items_lock:
                                item["status"] = res.get("status", "complete")
                                item["result"] = res
                            self.broadcast_event({
                                "type": "item_updated",
                                "id": item["id"],
                                "status": item["status"],
                                "result": res,
                            })

                    res = service.run(
                        source=source,
                        output=output,
                        name=name,
                        summary=summary,
                        context=context,
                        profile=profile or cfg["synthesis"]["context_profile"],
                        cancel=self.cancel,
                        notify=on_notify,
                    )
                    with self.items_lock:
                        item["status"] = res.get("status", "complete")
                        item["result"] = res

            except Exception as exc:
                self.broadcast_event({"type": "job_failed", "error": str(exc)})
            finally:
                self.progress_stage = "idle"
                self.broadcast_event({
                    "type": "job_finished",
                    "cancelled": self.cancel.is_set(),
                    "message": "Queue stopped" if self.cancel.is_set() else "Queue finished",
                })

        self.worker = threading.Thread(target=runner, daemon=False)
        self.worker.start()
        return {"ok": True, "started_count": len(targets)}

    def stop_processing(self) -> Dict[str, Any]:
        self.cancel.set()
        return {"ok": True, "message": "Stopping at next safe checkpoint."}

    # --- Watch Mode ---
    def start_watcher(self, folder: str, context: str = "", profile: Optional[str] = None) -> Dict[str, Any]:
        if self.is_watching():
            return {"ok": False, "error": "Watcher is already running."}

        folder_path = Path(folder).expanduser().resolve()
        if not folder_path.is_dir():
            return {"ok": False, "error": f"Folder does not exist: {folder}"}

        cfg = deepcopy(self.settings.data)
        service = JobService(cfg)
        service.snapshot_prompt()

        self.watcher_cancel.clear()
        self.watcher_folder = str(folder_path)

        def on_event(evt):
            if "result" in evt:
                res = evt["result"]
                source = Path(res["source"])
                with self.items_lock:
                    existing = next((i for i in self.items if i["source"] == str(source)), None)
                    if not existing:
                        self.add_paths([str(source)])
                        existing = next((i for i in self.items if i["source"] == str(source)), None)
                    if existing:
                        existing["status"] = res.get("status", "complete")
                        existing["result"] = res
            self.broadcast_event({"type": "watcher_event", "event": evt})

        def watch_runner():
            try:
                watcher = Watcher(
                    service=service,
                    folder=folder_path,
                    output_root=cfg["output"]["directory"],
                    summary=True,
                    context=context,
                    profile=profile,
                    notify=on_event,
                )
                self.watcher = watcher
                watcher.run(self.watcher_cancel)
            except Exception as exc:
                self.broadcast_event({"type": "watcher_error", "error": str(exc)})
            finally:
                self.watcher = None
                self.watcher_folder = None
                self.broadcast_event({"type": "watcher_stopped"})

        self.watcher_worker = threading.Thread(target=watch_runner, daemon=True)
        self.watcher_worker.start()
        return {"ok": True, "folder": str(folder_path)}

    def stop_watcher(self) -> Dict[str, Any]:
        self.watcher_cancel.set()
        return {"ok": True, "message": "Stopping watcher."}

    # --- Prompts & Diagnostics ---
    def get_prompt_info(self, mode: str) -> Dict[str, Any]:
        if mode not in MODES:
            raise ValueError(f"Unknown mode: {mode}")
        cfg = deepcopy(self.settings.data)
        cfg["synthesis"]["mode"] = mode
        template = load_template(cfg)
        builtin_path = BUILTINS / f"{mode}.txt"
        if not builtin_path.exists():
            builtin_path = template.path
        builtin_text = builtin_path.read_text(encoding="utf-8") if builtin_path.exists() else ""
        return {
            "mode": mode,
            "mode_name": MODES[mode],
            "template_path": str(template.path),
            "text": template.text,
            "builtin_text": builtin_text,
            "custom_folder": cfg["synthesis"]["prompt_directory"] or str(self.settings.path.parent / "audio_to_idea_prompts"),
        }

    def save_prompt(self, mode: str, text: str, custom_folder: Optional[str] = None) -> Dict[str, Any]:
        if mode not in MODES:
            raise ValueError(f"Unknown mode: {mode}")
        validated = validate_template(text)
        folder = Path(custom_folder or self.settings.data["synthesis"]["prompt_directory"] or (self.settings.path.parent / "audio_to_idea_prompts")).expanduser().resolve()
        
        # Guard against overwriting shipped builtins
        if folder.is_relative_to(BUILTINS.resolve()) or folder.is_relative_to((ROOT / "prompts").resolve()):
            raise ValueError("Choose a separate custom prompt folder outside application packages.")

        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{mode}.txt"
        atomic_write(path, validated.rstrip() + "\n")
        update_settings(self.settings.path, {"synthesis.prompt_directory": str(folder), "synthesis.prompt_file": None})
        self.settings.data["synthesis"].update(prompt_directory=str(folder), prompt_file=None)
        return {"ok": True, "path": str(path)}

    def preview_prompt(self, mode: str, text: str, item_id: Optional[str] = None, context: str = "", profile_path: Optional[str] = None) -> str:
        validated = validate_template(text)
        source = "यह एक sample recording है। Please review the inspection report for the bridge work."
        if item_id:
            with self.items_lock:
                item = next((i for i in self.items if i["id"] == item_id), None)
                if item and (item.get("result") or {}).get("transcript_path"):
                    data = read_json(item["result"]["transcript_path"])
                    source = "\n".join(f"[{s['id']}] {s['text']}" for s in data.get("segments", []))[:5000]

        profile_data = load_profile(profile_path or self.settings.data["synthesis"]["context_profile"], context)
        language = profile_data.get("output_language") or self.settings.data["synthesis"]["output_language"]
        if language == "source" and mode != "ideas_actions":
            from .rewriting import source_language
            language = source_language(re.sub(r"^\[S\d+\] ", "", source, flags=re.M))
        return Template(validated, Path(), mode).render(source, profile_data["background"], language)

    def run_doctor(self) -> Dict[str, Any]:
        return doctor(self.settings, include_discovery=True)

    def get_profiles(self) -> List[Dict[str, str]]:
        profiles = [{"label": "No profile", "value": ""}]
        profile_paths = sorted((ROOT / "profiles/audio_to_idea").glob("*.json")) + sorted((Path(__file__).parent / "example_profiles").glob("*.json"))
        for p in profile_paths:
            profiles.append({"label": p.stem.replace("_", " ").title(), "value": str(p)})
        return profiles

    # --- Native Desktop File / Folder Picker Bridge ---
    @staticmethod
    def browse_dialog(kind: str = "files") -> List[str]:
        """Launches native Linux GTK (zenity) or Tkinter picker in a subprocess/safe context."""
        # 1. Try zenity first (standard native GNOME/Ubuntu GTK dialog, ultra fast)
        if shutil.which("zenity"):
            try:
                if kind == "folder":
                    res = subprocess.run(
                        ["zenity", "--file-selection", "--directory", "--title=Select Audio Folder"],
                        capture_output=True, text=True, timeout=120
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        return [res.stdout.strip()]
                else:
                    res = subprocess.run(
                        [
                            "zenity", "--file-selection", "--multiple", "--separator=|",
                            "--title=Select Audio Files",
                            '--file-filter=Audio files | *.mp3 *.wav *.m4a *.aac *.flac *.ogg *.webm',
                            '--file-filter=All files | *'
                        ],
                        capture_output=True, text=True, timeout=120
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        return [p.strip() for p in res.stdout.strip().split("|") if p.strip()]
            except Exception:
                pass

        # 2. Fallback to python tkinter runner script
        try:
            cmd = [
                sys.executable, "-c",
                "import tkinter as tk, tkinter.filedialog as fd, json\n"
                "root = tk.Tk(); root.withdraw()\n"
                f"res = fd.askdirectory(title='Select Folder') if '{kind}' == 'folder' else fd.askopenfilenames(title='Select Audio Files')\n"
                "print(json.dumps([res] if isinstance(res, str) and res else list(res)))\n"
            ]
            out = subprocess.check_output(cmd, timeout=120, text=True)
            return json.loads(out.strip())
        except Exception as exc:
            print(f"[web_service] browse_dialog error: {exc}")
            return []


def urllib_quote(val: str) -> str:
    import urllib.parse
    return urllib.parse.quote(val)
