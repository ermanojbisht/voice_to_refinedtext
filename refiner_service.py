"""Thread-safe backend service for AI Voice Refiner desktop dashboard.

Connects the VoiceEngine audio recording, transcription, and refinement pipeline
to local web clients with state broadcasting.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from typing import Dict, Any, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from engine import VoiceEngine
import utils


class RefinerService:
    """Singleton service managing live voice recording, transcription, and refinement."""
    _instance: Optional["RefinerService"] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "RefinerService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self.script_dir = SCRIPT_DIR
        self.engine = VoiceEngine(self.script_dir)
        self.state_lock = threading.Lock()
        
        self.is_recording = False
        self.is_processing = False
        self.visual_state = "idle"  # idle | recording | processing | success | error
        self.status_message = "Ready to Record"
        self.last_refined_text = ""
        self.last_raw_text = ""
        self.last_duration = 0.0
        self.recent_clips: List[Dict[str, Any]] = []
        self._record_thread: Optional[threading.Thread] = None

    def get_status(self) -> Dict[str, Any]:
        with self.state_lock:
            active_preset = self.engine.get_active_preset()
            active_goal = self.engine.get_active_goal()
            presets = self.engine.config.get("ASR_PRESETS", {})
            goals = self.engine.config.get("REFINEMENT_GOALS", {})
            return {
                "visual_state": self.visual_state,
                "is_recording": self.is_recording,
                "is_processing": self.is_processing,
                "status_message": self.status_message,
                "active_preset": active_preset,
                "active_preset_label": presets.get(active_preset, {}).get("label", active_preset),
                "active_preset_desc": presets.get(active_preset, {}).get("description", ""),
                "active_goal": active_goal,
                "active_goal_label": goals.get(active_goal, {}).get("label", active_goal),
                "active_goal_desc": goals.get(active_goal, {}).get("description", ""),
                # Backward-compatibility fields
                "active_profile": active_preset,
                "language_mode": goals.get(active_goal, {}).get("output_lang", active_goal),
                "last_text": self.last_refined_text,
                "last_raw": self.last_raw_text,
                "last_duration": round(self.last_duration, 2),
                "word_count": len(self.last_refined_text.split()) if self.last_refined_text else 0,
                "recent_clips": list(self.recent_clips[-10:]),
                "global_hotkey": utils.get_global_hotkey(self.engine.config),
                "acoustic_suggestion": getattr(self.engine, "last_acoustic_suggestion", None),
                "acoustic_info": getattr(self.engine, "last_acoustic_info", None),
            }

    def start_recording(self) -> Dict[str, Any]:
        with self.state_lock:
            if self.is_recording or self.is_processing:
                return {"ok": False, "error": "Already recording or processing"}
            self.is_recording = True
            self.visual_state = "recording"
            self.status_message = "🎙 Listening... Speak in Hindi, English or mixed speech."

        def worker():
            start_time = time.monotonic()
            try:
                # 1. Record audio
                wav_path = self.engine.record()
                duration = time.monotonic() - start_time
                
                with self.state_lock:
                    self.is_recording = False
                    self.is_processing = True
                    self.visual_state = "processing"
                    self.status_message = "🧠 Transcribing with active preset..."

                # 2. Transcribe
                raw_text = self.engine.transcribe(wav_path)
                if not raw_text.strip():
                    with self.state_lock:
                        self.is_processing = False
                        self.visual_state = "error"
                        self.status_message = "No speech detected."
                    return

                # 3. Refine
                with self.state_lock:
                    self.status_message = "✨ Refining with active goal..."

                final_text = self.engine.refine(raw_text)

                # 4. Success actions
                with self.state_lock:
                    self.is_processing = False
                    self.visual_state = "success"
                    self.status_message = "Refinement complete!"
                    self.last_refined_text = final_text
                    self.last_raw_text = raw_text
                    self.last_duration = duration
                    clip = {
                        "id": f"clip_{int(time.time())}",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "text": final_text,
                        "raw": raw_text,
                        "words": len(final_text.split()),
                        "duration": round(duration, 1),
                        "preset": self.engine.get_active_preset(),
                        "goal": self.engine.get_active_goal(),
                    }
                    self.recent_clips.append(clip)

                # Copy to clipboard
                try:
                    subprocess.run(["xclip", "-selection", "clipboard"], input=final_text.encode("utf-8"), check=False, timeout=2)
                except Exception:
                    pass

                # Play completion sound if enabled
                if self.engine.config.get("FEATURES", {}).get("start_end_sounds", True):
                    complete_sound = os.path.join(self.script_dir, "sounds", "complete.oga")
                    if os.path.exists(complete_sound):
                        subprocess.run(["paplay", complete_sound], check=False, timeout=2)

            except Exception as exc:
                with self.state_lock:
                    self.is_recording = False
                    self.is_processing = False
                    self.visual_state = "error"
                    self.status_message = f"Error: {exc}"

        self._record_thread = threading.Thread(target=worker, daemon=True)
        self._record_thread.start()
        return {"ok": True, "state": "recording"}

    def stop_recording(self) -> Dict[str, Any]:
        with self.state_lock:
            if not self.is_recording:
                return {"ok": False, "error": "Not currently recording"}
            self.status_message = "Stopping recording & processing..."
        self.engine.stop_recording()
        return {"ok": True, "state": "stopping"}

    def reprocess_last_sync(self, preset: Optional[str] = None, goal: Optional[str] = None) -> Dict[str, Any]:
        """Synchronously re-processes cached last recording, updates state/clips, copies to clipboard, and returns result."""
        with self.state_lock:
            if self.is_recording or self.is_processing:
                return {"ok": False, "error": "Cannot re-process while recording or processing"}
            self.is_processing = True
            self.visual_state = "processing"
            self.status_message = "🔁 Re-processing last audio recording..."

        start_time = time.monotonic()
        try:
            res = self.engine.reprocess_last_audio(preset=preset, goal=goal)
            duration = time.monotonic() - start_time
            if not res.get("ok"):
                with self.state_lock:
                    self.is_processing = False
                    self.visual_state = "error"
                    self.status_message = f"Re-process failed: {res.get('error')}"
                return res

            raw_text = res.get("raw_text", "")
            final_text = res.get("final_text", "")

            with self.state_lock:
                self.is_processing = False
                self.visual_state = "success"
                self.status_message = "Re-processing complete!"
                self.last_refined_text = final_text
                self.last_raw_text = raw_text
                self.last_duration = duration
                clip = {
                    "id": f"clip_{int(time.time())}",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "text": final_text,
                    "raw": raw_text,
                    "words": len(final_text.split()),
                    "duration": round(duration, 1),
                    "preset": res.get("preset"),
                    "goal": res.get("goal"),
                    "reprocessed": True
                }
                self.recent_clips.append(clip)

            try:
                subprocess.run(["xclip", "-selection", "clipboard"], input=final_text.encode("utf-8"), check=False, timeout=2)
            except Exception:
                pass

            return {
                **res,
                "ok": True,
                "final_text": final_text,
                "text": final_text,
                "clip": clip,
            }

        except Exception as exc:
            with self.state_lock:
                self.is_processing = False
                self.visual_state = "error"
                self.status_message = f"Error: {exc}"
            return {"ok": False, "error": str(exc)}

    def reprocess_last(self, preset: Optional[str] = None, goal: Optional[str] = None) -> Dict[str, Any]:
        """Asynchronously re-runs the cached last recording through specified or active Preset and Goal."""
        with self.state_lock:
            if self.is_recording or self.is_processing:
                return {"ok": False, "error": "Cannot re-process while recording or processing"}

        def worker():
            self.reprocess_last_sync(preset=preset, goal=goal)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        return {"ok": True, "state": "processing"}

    def cycle_preset(self) -> str:
        presets = list(self.engine.config.get("ASR_PRESETS", {}).keys())
        if not presets:
            presets = ["smart_bilingual", "instant_english", "instant_hindi", "roman_hinglish"]
        cur = self.engine.get_active_preset()
        next_p = presets[(presets.index(cur) + 1) % len(presets)] if cur in presets else presets[0]
        self.set_preset(next_p)
        return next_p

    def set_preset(self, preset_key: str) -> bool:
        self.engine.set_active_preset(preset_key)
        self._save_config_patch({
            "ACTIVE_ASR_PRESET": preset_key,
            "ACTIVE_MODEL_PROFILE": preset_key,
            "ASR_ENGINE": self.engine.config.get("ASR_ENGINE", "faster_whisper")
        })
        return True

    def cycle_goal(self) -> str:
        goals = list(self.engine.config.get("REFINEMENT_GOALS", {}).keys())
        if not goals:
            goals = ["clean_bilingual", "official_english", "official_hindi", "concise_summary", "ideas_actions", "roman_hinglish"]
        cur = self.engine.get_active_goal()
        next_g = goals[(goals.index(cur) + 1) % len(goals)] if cur in goals else goals[0]
        self.set_goal(next_g)
        return next_g

    def set_goal(self, goal_key: str) -> bool:
        self.engine.set_active_goal(goal_key)
        goals = self.engine.config.get("REFINEMENT_GOALS", {})
        target_lang = goals.get(goal_key, {}).get("output_lang", "bilingual")
        self._save_config_patch({
            "ACTIVE_REFINEMENT_GOAL": goal_key,
            "LANGUAGE_MODE": target_lang,
            "MODE": "translate" if goals.get(goal_key, {}).get("translate") else "refine"
        })
        return True

    def cycle_language_mode(self) -> str:
        modes = ["bilingual", "pure_english", "pure_hindi", "roman_hinglish"]
        cur = self.engine.config.get("LANGUAGE_MODE", "bilingual")
        next_m = modes[(modes.index(cur) + 1) % len(modes)] if cur in modes else modes[0]
        mode_to_goal = {
            "bilingual": "clean_bilingual",
            "pure_english": "official_english",
            "pure_hindi": "official_hindi",
            "roman_hinglish": "roman_hinglish"
        }
        self.set_goal(mode_to_goal.get(next_m, "clean_bilingual"))
        return next_m

    def cycle_asr_profile(self) -> str:
        return self.cycle_preset()

    def record_external_clip(
        self,
        raw_text: str,
        final_text: str,
        duration: float = 0.0,
        preset: Optional[str] = None,
        goal: Optional[str] = None,
        acoustic_suggestion: Optional[dict] = None,
        acoustic_info: Optional[dict] = None
    ):
        """Records a clip processed externally (e.g. by tray app or global hotkey) into web dashboard state."""
        with self.state_lock:
            self.is_recording = False
            self.is_processing = False
            self.visual_state = "success"
            self.status_message = "Refinement Complete!"
            self.last_refined_text = final_text
            self.last_raw_text = raw_text
            self.last_duration = duration
            if acoustic_suggestion is not None:
                self.engine.last_acoustic_suggestion = acoustic_suggestion
            if acoustic_info is not None:
                self.engine.last_acoustic_info = acoustic_info
            p_val = str(preset or (self.engine.get_active_preset() if hasattr(self.engine, "get_active_preset") else "smart_bilingual"))
            g_val = str(goal or (self.engine.get_active_goal() if hasattr(self.engine, "get_active_goal") else "clean_bilingual"))
            clip = {
                "id": f"clip_{int(time.time())}",
                "timestamp": time.strftime("%H:%M:%S"),
                "text": final_text,
                "raw": raw_text,
                "words": len(final_text.split()),
                "duration": round(duration, 1),
                "preset": p_val,
                "goal": g_val,
                "acoustic_suggestion": acoustic_suggestion
            }
            self.recent_clips.append(clip)
            if len(self.recent_clips) > 50:
                self.recent_clips.pop(0)

    def _save_config_patch(self, patch: Dict[str, Any]):
        cfg_path = os.path.join(self.script_dir, "config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.update(patch)
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.engine.reload_config()
        except Exception as exc:
            print(f"[refiner_service] Error updating config: {exc}")
