"""Backend service for Executive Evening Review Web Studio.

Provides thread-safe session management, voice clip staging, inline editing,
field audio uploads, and live Obsidian vault synchronization.
"""
from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Dict, Any, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import review_engine
from engine import VoiceEngine
import utils as _utils


class ReviewService:
    """Singleton service managing live Evening Review sessions and REST interactions."""
    _instance: Optional["ReviewService"] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ReviewService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self.script_dir = SCRIPT_DIR
        self.engine: Optional[VoiceEngine] = None
        self._engine_lock = threading.RLock()
        self.state_lock = threading.RLock()
        
        # Audio recording tracking
        self.is_recording = False
        self.record_thread: Optional[threading.Thread] = None
        self.last_recorded_clip = ""
        self.last_audio_duration = 0.0
        self.last_completed_date: Optional[str] = None

    def _get_engine(self) -> VoiceEngine:
        with self._engine_lock:
            if self.engine is None:
                self.engine = VoiceEngine(self.script_dir)
            return self.engine

    def get_state(self) -> Dict[str, Any]:
        """Returns comprehensive state for the web studio."""
        with self.state_lock:
            config = review_engine.load_review_config(self.script_dir)
            active, state = review_engine.is_review_active(self.script_dir)
            if not active or state is None:
                # Review not active; return dormant session summary
                today_str = datetime.date.today().isoformat()
                streak_info = review_engine.load_streak(self.script_dir)
                trend_info = review_engine.get_focus_word_counts(self.script_dir, n=7)
                return {
                    "active": False,
                    "date": today_str,
                    "streak_current": streak_info.get("current", 0),
                    "steps": config.get("review_steps", []),
                    "step_count": len(config.get("review_steps", [])),
                    "focus_trend": trend_info,
                    "is_recording": self.is_recording,
                    "global_hotkey": _utils.get_global_hotkey(script_dir=self.script_dir),
                }

            current_step = review_engine.get_current_step(state, config)
            step_count = review_engine.get_step_count(config)
            step_idx = state.get("current_step_index", 0)
            accumulated_raw = state.get("accumulated_raw", [])

            # Format clips with IDs, word counts, and text for UI staging
            clips = [
                {
                    "index": i,
                    "id": f"clip_{i}",
                    "text": clip_text,
                    "words": len(clip_text.split()),
                    "chars": len(clip_text),
                }
                for i, clip_text in enumerate(accumulated_raw)
            ]

            streak_info = review_engine.load_streak(self.script_dir)
            trend_info = review_engine.get_focus_word_counts(self.script_dir, n=7)

            # Carry-forward tasks (Step 5)
            carry_tasks = state.get("carryforward_tasks", [])

            return {
                "active": True,
                "date": state.get("date", datetime.date.today().isoformat()),
                "started_at": state.get("started_at"),
                "current_step_index": step_idx,
                "step_count": step_count,
                "current_step": current_step,
                "steps": config.get("review_steps", []),
                "clips": clips,
                "clip_count": len(clips),
                "awaiting_more": state.get("awaiting_more", False),
                "processing": state.get("processing", False),
                "is_recording": self.is_recording,
                "context_brief": state.get("context_brief"),
                "context_brief_en": state.get("context_brief_en") or state.get("context_brief", ""),
                "context_brief_hi": state.get("context_brief_hi", ""),
                "context_ready": state.get("context_ready", False),
                "streak_current": state.get("streak_current", streak_info.get("current", 0)),
                "carryforward_tasks": carry_tasks,
                "carryforward_date": state.get("carryforward_date", ""),
                "focus_trend": trend_info,
                "step_times": state.get("step_times", []),
                "interview_raw": state.get("interview_raw", {}),
                "global_hotkey": _utils.get_global_hotkey(script_dir=self.script_dir),
                "acoustic_suggestion": getattr(self._get_engine(), "last_acoustic_suggestion", None),
            }

    def regen_brief(self) -> Dict[str, Any]:
        """Busts context brief cache and regenerates for the active session."""
        config = review_engine.load_review_config(self.script_dir)
        threading.Thread(target=review_engine.regenerate_brief, args=(self.script_dir, config), daemon=True).start()
        return {"ok": True, "message": "Regenerating context brief..."}

    def open_in_obsidian(self) -> Dict[str, Any]:
        """Opens active daily note in Obsidian desktop app."""
        config = review_engine.load_review_config(self.script_dir)
        state = review_engine.load_state()
        date_str = state.get("date", datetime.date.today().isoformat()) if state else datetime.date.today().isoformat()
        daily_note_path = review_engine.get_daily_note_path(self.script_dir, config, date_str)
        try:
            subprocess.Popen(["xdg-open", daily_note_path])
            return {"ok": True, "path": daily_note_path}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "path": daily_note_path}

    def start_review(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Initializes a new review session."""
        with self.state_lock:
            active, _ = review_engine.is_review_active(self.script_dir)
            if active:
                return {"ok": True, "resumed": True, "state": self.get_state()}

            if date_str:
                try:
                    datetime.date.fromisoformat(date_str)
                except ValueError:
                    date_str = datetime.date.today().isoformat()
            else:
                date_str = datetime.date.today().isoformat()

            review_engine.initialize_review(self.script_dir, date_str=date_str)
            return {"ok": True, "date": date_str, "state": self.get_state()}

    def start_recording(self) -> Dict[str, Any]:
        """Starts live microphone recording for the current step."""
        with self.state_lock:
            active, state = review_engine.is_review_active(self.script_dir)
            if not active or state is None:
                return {"ok": False, "error": "No review session is currently active."}
            if self.is_recording:
                return {"ok": False, "error": "Already recording audio."}

            self.is_recording = True

        def worker():
            t0 = time.monotonic()
            try:
                eng = self._get_engine()
                wav_path = eng.record()
                duration = time.monotonic() - t0

                # Transcribe
                raw_text = eng.transcribe(wav_path)
                with self.state_lock:
                    self.is_recording = False
                    self.last_audio_duration = duration
                    self.last_recorded_clip = raw_text

                    if raw_text.strip():
                        # Append to state's accumulated_raw
                        fresh_state = review_engine.load_state()
                        if fresh_state:
                            review_engine.accumulate_clip(fresh_state, raw_text.strip())

            except Exception as exc:
                with self.state_lock:
                    self.is_recording = False
                print(f"[review_service] Recording worker exception: {exc}")

        self.record_thread = threading.Thread(target=worker, daemon=True)
        self.record_thread.start()
        return {"ok": True, "state": "recording"}

    def stop_recording(self) -> Dict[str, Any]:
        """Stops active microphone recording, triggers ASR and stages clip."""
        with self.state_lock:
            if not self.is_recording:
                return {"ok": False, "error": "Not currently recording."}

        eng = self._get_engine()
        eng.stop_recording()

        # Wait up to 5s for worker to finish ASR transcription
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=5.0)

        return {
            "ok": True,
            "clip": self.last_recorded_clip,
            "duration": round(self.last_audio_duration, 1),
            "state": self.get_state(),
            "acoustic_suggestion": getattr(self._get_engine(), "last_acoustic_suggestion", None),
        }

    def upload_clip(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Transcribes an uploaded audio file (e.g. from site visit) and stages clip."""
        with self.state_lock:
            active, state = review_engine.is_review_active(self.script_dir)
            if not active or state is None:
                return {"ok": False, "error": "No active review session."}

        # Save to temporary file
        suffix = os.path.splitext(filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            # Convert to 16kHz mono WAV if needed via ffmpeg
            wav_path = tmp_path
            if not tmp_path.lower().endswith(".wav"):
                wav_target = tmp_path + ".converted.wav"
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_target],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                )
                wav_path = wav_target

            eng = self._get_engine()
            raw_text = eng.transcribe(wav_path)
            if not raw_text.strip():
                return {"ok": False, "error": "No discernible speech detected in uploaded audio."}

            with self.state_lock:
                fresh_state = review_engine.load_state()
                if fresh_state:
                    review_engine.accumulate_clip(fresh_state, raw_text.strip())

            return {
                "ok": True,
                "text": raw_text.strip(),
                "state": self.get_state(),
                "acoustic_suggestion": getattr(eng, "last_acoustic_suggestion", None)
            }

        except Exception as exc:
            return {"ok": False, "error": f"Audio processing failed: {exc}"}
        finally:
            for p in (tmp_path, tmp_path + ".converted.wav"):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

    def update_clip(self, index: int, new_text: str) -> Dict[str, Any]:
        """Updates text of an existing staged clip (inline correction)."""
        with self.state_lock:
            state = review_engine.load_state()
            if not state:
                return {"ok": False, "error": "No active review."}

            clips = state.get("accumulated_raw", [])
            if 0 <= index < len(clips):
                clips[index] = new_text.strip()
                state["accumulated_raw"] = clips
                review_engine._save_state(state)
                return {"ok": True, "state": self.get_state()}
            return {"ok": False, "error": f"Invalid clip index: {index}"}

    def delete_clip(self, index: int) -> Dict[str, Any]:
        """Removes a specific clip from the staging buffer."""
        with self.state_lock:
            state = review_engine.load_state()
            if not state:
                return {"ok": False, "error": "No active review."}

            clips = state.get("accumulated_raw", [])
            if 0 <= index < len(clips):
                deleted = clips.pop(index)
                state["accumulated_raw"] = clips
                if not clips:
                    state["awaiting_more"] = False
                review_engine._save_state(state)
                return {"ok": True, "deleted": deleted, "state": self.get_state()}
            return {"ok": False, "error": f"Invalid clip index: {index}"}

    def advance_step(self) -> Dict[str, Any]:
        """Structures accumulated clips and advances to the next step or synthesizes."""
        with self.state_lock:
            active, state = review_engine.is_review_active(self.script_dir)
            if not active or state is None:
                return {"ok": False, "error": "No active review."}
            cur_date = state.get("date")

        config = review_engine.load_review_config(self.script_dir)
        eng = self._get_engine()
        success, error, still_active = review_engine.structure_and_advance(self.script_dir, eng, config)
        if not still_active and cur_date:
            self.last_completed_date = cur_date
        return {
            "ok": success,
            "error": error,
            "still_active": still_active,
            "state": self.get_state()
        }

    def skip_step(self) -> Dict[str, Any]:
        """Skips the active step and fills fallback default."""
        with self.state_lock:
            state = review_engine.load_state()
            if not state:
                return {"ok": False, "error": "No active review."}

        config = review_engine.load_review_config(self.script_dir)
        review_engine.skip_step(self.script_dir, state, config)
        still_active, _ = review_engine.is_review_active(self.script_dir)
        return {"ok": True, "still_active": still_active, "state": self.get_state()}

    def redo_step(self) -> Dict[str, Any]:
        """Clears accumulated clips and restarts the current step."""
        with self.state_lock:
            state = review_engine.load_state()
            if not state:
                return {"ok": False, "error": "No active review."}

        config = review_engine.load_review_config(self.script_dir)
        review_engine.redo_step(self.script_dir, state, config)
        return {"ok": True, "state": self.get_state()}

    def cancel_review(self) -> Dict[str, Any]:
        """Aborts the review session."""
        review_engine.cancel_review(self.script_dir)
        return {"ok": True, "state": self.get_state()}

    def resolve_task(self, task_text: str, note_date_str: str) -> Dict[str, Any]:
        """Marks an open carry-forward task as completed."""
        config = review_engine.load_review_config(self.script_dir)
        success = review_engine.mark_task_done(self.script_dir, config, task_text, note_date_str)
        # Refresh carryforward tasks list in state
        with self.state_lock:
            state = review_engine.load_state()
            if state:
                state["carryforward_tasks"] = review_engine.get_pending_tasks(self.script_dir, config)
                review_engine._save_state(state)
        return {"ok": success, "task": task_text, "state": self.get_state()}

    def _find_latest_review_date(self, config: Dict[str, Any]) -> str:
        """Finds the most appropriate review date (last completed or most recent daily note)."""
        if self.last_completed_date:
            return self.last_completed_date

        log_path = os.path.join(self.script_dir, "review_log.json")
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                if isinstance(logs, list) and logs:
                    for entry in reversed(logs):
                        s_date = entry.get("session_date")
                        if s_date:
                            p = review_engine.get_daily_note_path(self.script_dir, config, s_date)
                            if os.path.exists(p):
                                return s_date
            except Exception:
                pass

        today_str = datetime.date.today().isoformat()
        if os.path.exists(review_engine.get_daily_note_path(self.script_dir, config, today_str)):
            return today_str

        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        if os.path.exists(review_engine.get_daily_note_path(self.script_dir, config, yesterday_str)):
            return yesterday_str

        return today_str

    def get_note_preview(self) -> Dict[str, Any]:
        """Reads and returns the active daily note Markdown content with real-time draft assembly."""
        config = review_engine.load_review_config(self.script_dir)
        state = review_engine.load_state()

        if state and state.get("date"):
            date_str = state["date"]
            is_active = True
        else:
            date_str = self._find_latest_review_date(config)
            is_active = False

        daily_note_path = review_engine.get_daily_note_path(self.script_dir, config, date_str)

        raw_content = ""
        if os.path.exists(daily_note_path):
            try:
                with open(daily_note_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()
            except Exception as exc:
                return {"ok": False, "error": str(exc), "date": date_str}
        else:
            dt = datetime.date.fromisoformat(date_str)
            prev_day = (dt - datetime.timedelta(days=1)).isoformat()
            next_day = (dt + datetime.timedelta(days=1)).isoformat()
            raw_content = (
                f"---\ncreation date: {date_str}\n---\n\n"
                f"<< [[{prev_day}]] | [[{next_day}]] >>\n\n"
                f"# {date_str}\n\n"
                f"### Movement\n\n"
                f"### Meeting\n\n"
                f"### Achievements\n\n"
                f"### Tomorrow's Priorities\n\n"
                f"### Focus Word\n\n"
            )

        # If review is active, merge in-flight interview text into empty sections
        if is_active and state:
            interview_raw = state.get("interview_raw", {})
            current_idx = state.get("current_step_index", 0)
            steps = config.get("review_steps", [])
            current_clips = state.get("accumulated_raw", [])

            section_drafts = {}
            for step in steps:
                if step.get("isolate_file", False):
                    continue
                step_id = str(step.get("step_id", step.get("section_name", "")))
                sec_name = step.get("section_name", "")
                if not sec_name:
                    continue
                if step_id in interview_raw and interview_raw[step_id].strip():
                    section_drafts[sec_name] = interview_raw[step_id].strip()

            if 0 <= current_idx < len(steps):
                cur_step = steps[current_idx]
                if not cur_step.get("isolate_file", False):
                    cur_sec = cur_step.get("section_name", "")
                    if cur_sec and current_clips:
                        cur_text = "\n".join(current_clips).strip()
                        if cur_text:
                            section_drafts[cur_sec] = cur_text

            for sec_name, draft_text in section_drafts.items():
                pattern = rf"(###\s+{re.escape(sec_name)}\s*\n)(?:\s*\n)*(?=###|\Z)"
                if re.search(pattern, raw_content):
                    raw_content = re.sub(pattern, rf"\1{draft_text}\n\n", raw_content, count=1)

        return {
            "ok": True,
            "exists": os.path.exists(daily_note_path),
            "date": date_str,
            "path": daily_note_path,
            "content": raw_content,
            "is_active": is_active,
            "synthesising": bool(state.get("synthesising", False)) if state else False
        }

    def replay_narration(self) -> Dict[str, Any]:
        """Replays narration of the current step's conversational prompt."""
        config = review_engine.load_review_config(self.script_dir)
        state = review_engine.load_state()
        if not state:
            return {"ok": False, "error": "No active review."}

        step = review_engine.get_current_step(state, config)
        if not step:
            return {"ok": False, "error": "No current step."}

        # Select prompt variant
        variants = step.get("narration_variants", [])
        text = variants[0] if variants else step.get("prompt_notification", "")
        threading.Thread(target=review_engine.narrate, args=(text, config), daemon=True).start()
        return {"ok": True, "prompt": text}

    def stop_narration(self) -> Dict[str, Any]:
        """Stops Piper / espeak voice narration."""
        review_engine.stop_narration()
        return {"ok": True}
