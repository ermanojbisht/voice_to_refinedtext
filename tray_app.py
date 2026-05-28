#!/usr/bin/env python3
import os
import pystray
from PIL import Image, ImageDraw
from pynput import keyboard
import threading
import subprocess
import time
import json
import datetime
from engine import VoiceEngine
import review_engine
import sys
import signal

import utils as _utils

_AUDIO_QUALITY_RATIO = 0.5   # WAV RMS must be >= SILENCE_THRESHOLD * this ratio

# Module-level logger — file handler added in VoiceAssistantTray.__init__()
_logger = _utils.get_logger("tray")


def _tlog(msg):
    """Compatibility shim — all existing call sites use _tlog()."""
    _logger.info(msg)

# ── Tray application ──────────────────────────────────────────────────────────

class VoiceAssistantTray:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(self.script_dir, "review_debug.log")
        _utils.get_logger("tray", log_path)        # attach file handler to _logger
        review_engine.init_logging(self.script_dir)
        _tlog("=" * 50)
        _tlog("VoiceAssistantTray starting")
        self.engine = VoiceEngine(self.script_dir)

        # App state flags
        self.is_recording = False
        self.running = True

        # Review state
        self.is_in_review = False
        self.review_config = None
        self.review_state = None

        # Icons
        self.icons = {
            "idle":       self.create_status_icon("#45475a"),  # Gray
            "recording":  self.create_status_icon("#f38ba8"),  # Red
            "processing": self.create_status_icon("#89b4fa"),  # Blue
            "review":     self.create_status_icon("#a6e3a1"),  # Green
        }

        # Build tray icon with single static menu (dynamic callables)
        self.icon = pystray.Icon(
            "AI Voice Refiner",
            self.icons["idle"],
            menu=self._build_static_menu()
        )

        # Hotkey listener (works on X11; on Wayland the GNOME shortcut + SIGUSR1 is used)
        self.pressed_keys = set()
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

        # Startup: resume or expire any stale review session
        result, state, cfg = review_engine.check_startup_state(self.script_dir)
        if result == "resume":
            self.is_in_review = True
            self.review_state = state
            self.review_config = cfg
            self.update_icon("review")
            review_engine.send_step_notification(state, cfg)
            _tlog(f"Resumed review session at step {state.get('current_step_index')}")
        elif result == "expired":
            _tlog("Stale review session expired on startup")

        # Voice wake-word listener (opt-in via voice_control: true in review_config.json)
        # Initialized after check_startup_state so self.review_config is already set.
        self._wake_listener = None
        self._init_wake_listener()

    def _get_active_config(self):
        """Return the current review config — live session config if active, else reload from disk."""
        return self.review_config or review_engine.load_review_config(self.script_dir)

    def _init_wake_listener(self):
        cfg = self._get_active_config()
        if not cfg.get("voice_control", False):
            return
        try:
            from voice_control import WakeWordListener
            self._wake_listener = WakeWordListener()
            self._wake_listener.start(
                cfg.get("voice_control_threshold", 500),
                lambda: review_engine.is_narrating() or self.is_in_review,
                review_engine.stop_narration,
                lambda: review_engine.replay_narration(self._get_active_config()),
                next_fn=lambda: self.next_step_review() if self.is_in_review else None,
                skip_fn=lambda: self.skip_review_step() if self.is_in_review else None,
            )
            _tlog("voice_control: wake word listener started")
        except ImportError:
            _tlog("voice_control: voice_control module not found — skipping")
        except Exception as exc:
            _tlog(f"voice_control: init failed — {exc}")

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_static_menu(self):
        """Single static menu; all text/visibility use live callables.
        pystray re-evaluates on every update_menu() — no rebuild needed."""

        def _step_label(item):
            if not self.is_in_review or not self.review_state or not self.review_config:
                return "Review in progress"
            total = review_engine.get_step_count(self.review_config)
            step = review_engine.get_current_step(self.review_state, self.review_config)
            idx = self.review_state.get("current_step_index", 0)
            if step:
                name = step["section_name"]
                clips = len(self.review_state.get("accumulated_raw", []))
                if self.review_state.get("awaiting_more", False):
                    clip_label = f" ({clips} clip{'s' if clips != 1 else ''})"
                    return f"Step {idx+1}/{total}: {name} \u2713{clip_label}"
                return f"Step {idx+1}/{total}: {name}"
            return "Review in progress"

        def _evening_review_enabled(item):
            return self.engine.config.get("FEATURES", {}).get("evening_review", True)
        def _in_review(item):           return self.is_in_review
        def _not_in_review(item):       return not self.is_in_review
        def _awaiting(item):            return self.is_in_review and bool(self.review_state and self.review_state.get("awaiting_more"))
        def _not_awaiting(item):        return self.is_in_review and not bool(self.review_state and self.review_state.get("awaiting_more"))
        def _mode_label(item):          return f"Mode: {self.engine.config.get('MODE', 'refine').capitalize()}"
        def _has_morning_brief(item):
            import morning_brief as _mb
            return not self.is_in_review and _mb.load_brief_state() is not None
        def _start_review_visible(item):
            return not self.is_in_review and _evening_review_enabled(item)

        return pystray.Menu(
            # ── Review mode ──
            pystray.MenuItem(_step_label,          None,                    enabled=False, visible=_in_review),
            pystray.MenuItem("Next Step",          self.next_step_review,                  visible=_awaiting),
            pystray.MenuItem("Skip This Step",     self.skip_review_step,                  visible=_not_awaiting),
            pystray.MenuItem("Redo This Step",     self.redo_review_step,                  visible=_in_review),
            pystray.MenuItem("Cancel Review",      self.cancel_review,                     visible=_in_review),
            pystray.Menu.SEPARATOR,
            # ── Normal mode ──
            pystray.MenuItem("Start Recording",        self.toggle_recording,               visible=_not_in_review),
            pystray.MenuItem(_mode_label,              self.cycle_mode,                     visible=_not_in_review),
            pystray.MenuItem("Start Evening Review",   self.start_review,                   visible=_start_review_visible),
            pystray.MenuItem("🌅 Replay Morning Brief", self.replay_morning_brief,          visible=_has_morning_brief),
            pystray.MenuItem("Open Dashboard",         self.open_gui,                       visible=_not_in_review),
            pystray.MenuItem("Settings",               self.open_settings,                  visible=_not_in_review),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.exit_app)
        )

    # ── Hotkey listener ───────────────────────────────────────────────────────

    def _ctrl(self):
        return any(k in self.pressed_keys for k in (
            keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r))

    def _alt(self):
        return any(k in self.pressed_keys for k in (
            keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r))

    def on_press(self, key):
        # Only track modifier keys and the three hotkey chars — everything else
        # is dead weight and would grow pressed_keys unboundedly over a session.
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                   keyboard.Key.alt,  keyboard.Key.alt_l,  keyboard.Key.alt_r):
            self.pressed_keys.add(key)
        elif hasattr(key, "char") and key.char in ("v", "s", "r"):
            self.pressed_keys.add(key)
        if not (self._ctrl() and self._alt()):
            return
        if hasattr(key, "char"):
            if key.char == "v":
                self.toggle_recording()
            elif key.char == "s":
                threading.Thread(target=review_engine.stop_narration, daemon=True).start()
            elif key.char == "r":
                threading.Thread(target=review_engine.replay_narration,
                                 args=(self._get_active_config(),), daemon=True).start()

    def on_release(self, key):
        self.pressed_keys.discard(key)

    # ── Icon helpers ──────────────────────────────────────────────────────────

    def create_status_icon(self, color):
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill=color)
        return image

    def update_icon(self, state_name):
        self.icon.icon = self.icons.get(state_name, self.icons["idle"])

    def _refresh_menu(self):
        try:
            self.icon.update_menu()
        except Exception as e:
            _tlog(f"_refresh_menu: warning (non-fatal): {e}")

    # ── Recording ─────────────────────────────────────────────────────────────

    def toggle_recording(self):
        if not self.is_recording:
            threading.Thread(target=self.run_full_process, daemon=True).start()
        elif self.is_recording:
            self.engine.stop_recording()

    def _notify(self, title, message):
        try:
            subprocess.run(
                ["notify-send", "-i", "dialog-information", "-t", "4000", title, message],
                timeout=5, check=False
            )
        except Exception:
            print(f"[{title}] {message}")

    def run_full_process(self):
        """Record → Transcribe → route to review accumulation or normal clipboard."""
        try:
            self.is_recording = True
            self.update_icon("recording")
            _tlog(f"run_full_process started. is_in_review={self.is_in_review}")

            wav_path = self.engine.record()

            self.is_recording = False

            # Audio quality gate — reject recordings that are too quiet to transcribe
            if not self._check_audio_quality(wav_path):
                self.update_icon("review" if self.is_in_review else "idle")
                return

            self.update_icon("processing")

            # Narrate processing so user knows recording was captured
            if self.is_in_review and self.review_config:
                review_engine.narrate("Processing.", self.review_config)

            self._notify("Voice Refiner", "Transcribing audio...")
            raw_text = self.engine.transcribe(wav_path)
            _tlog(f"Transcription done: len={len(raw_text)} preview='{raw_text[:80]}'")

            if not raw_text.strip():
                self._notify("Voice Refiner", "No speech detected. Try again.")
                _tlog("No speech detected")
                self.update_icon("review" if self.is_in_review else "idle")
                return

            if self.is_in_review:
                _tlog("Routing: REVIEW MODE")
                self._handle_review_step(raw_text)
            else:
                _tlog("Routing: NORMAL MODE")
                self._run_normal_mode(raw_text)

            self.update_icon("review" if self.is_in_review else "idle")

        except Exception as e:
            import traceback
            _tlog(f"EXCEPTION in run_full_process:\n{traceback.format_exc()}")
            self._notify("Voice Refiner — Error", str(e)[:120])
            self.is_recording = False
            self.update_icon("review" if self.is_in_review else "idle")

    def _check_audio_quality(self, wav_path):
        """Return False (and warn) if the WAV RMS is below half the silence threshold."""
        import wave
        import numpy as np
        try:
            with wave.open(wav_path, "rb") as wf:
                raw = wf.readframes(wf.getnframes())
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            if len(samples) == 0:
                return True
            rms = float(np.sqrt(np.mean(samples ** 2)))
            threshold = self.engine.config.get("SILENCE_THRESHOLD", 300) * _AUDIO_QUALITY_RATIO
            if rms < threshold:
                _tlog(f"Audio quality low: rms={rms:.1f} threshold={threshold:.1f}")
                cfg = self._get_active_config() if self.is_in_review else {}
                review_engine.narrate("Recording seems too quiet, please try again.", cfg)
                self._notify("Voice Refiner", "Recording too quiet — please try again.")
                return False
        except Exception as e:
            _tlog(f"Audio quality check error: {e}")
        return True

    def _handle_review_step(self, raw_text):
        """Accumulate raw transcription into state. No LLM call here — deferred to Next Step."""
        _tlog("_handle_review_step: accumulating raw text")
        if self.review_config is None:
            # cancel_review() fired between is_in_review check and this call — nothing to do
            _tlog("_handle_review_step: review_config gone (cancel race), ignoring")
            return

        # Always reload state from disk (may have changed via menu actions)
        _, fresh_state = review_engine.is_review_active(self.script_dir)
        if fresh_state is None:
            # State vanished while recording was in flight (session expired, cancelled,
            # or completed by another path). Processing this audio as normal voice input
            # would be wrong — review content must not end up on the clipboard.
            _tlog("WARNING: review state gone mid-recording, discarding orphaned transcript")
            self._notify("Evening Review", "Review session ended — recording discarded.")
            self._review_finished()
            return

        self.review_state = fresh_state
        step = review_engine.get_current_step(fresh_state, self.review_config)
        if step is None:
            _tlog("ERROR: get_current_step returned None")
            self._notify("Voice Refiner", "Review error: could not get current step.")
            return

        # Accumulate raw text in state file via public API
        self.review_state = review_engine.accumulate_clip(self.review_state, raw_text)

        clip_count = len(self.review_state["accumulated_raw"])
        step_name = step.get("section_name", "this step")
        _tlog(f"Accumulated clip {clip_count} for step '{step_name}'")

        review_engine.send_awaiting_notification(self.review_state, self.review_config)
        self._refresh_menu()

    def _run_normal_mode(self, raw_text):
        """Normal mode: refine → clipboard → optional direct typing."""
        _tlog("_run_normal_mode: refining")
        self._notify("Voice Refiner", "Refining text with AI...")
        final_text = self.engine.refine(raw_text)
        self._notify("Voice Refiner", "Done! Text copied to clipboard.")
        _tlog(f"_run_normal_mode: refined, len={len(final_text)}")
        features = self.engine.config.get("FEATURES", {})
        if features.get("clipboard_output", True):
            try:
                subprocess.run("xclip -selection clipboard", input=final_text.encode(), shell=True, check=False)
            except Exception:
                try:
                    subprocess.run("xsel --clipboard --input", input=final_text.encode(), shell=True, check=False)
                except Exception:
                    pass
        try:
            subprocess.run(["paplay", os.path.join(self.script_dir, "sounds", "complete.oga")], check=False)
        except Exception:
            pass
        if features.get("direct_typing", False):
            self.engine.type_text(final_text)

    # ── Review controls ───────────────────────────────────────────────────────

    def _ask_review_date(self):
        """Show a small dialog so the user can pick the review date.
        Returns a YYYY-MM-DD string, or None if the user cancelled."""
        import tkinter as tk
        from tkinter import simpledialog, messagebox
        today = datetime.date.today().isoformat()
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)
        answer = simpledialog.askstring(
            "Evening Review — Date",
            f"Review date (YYYY-MM-DD).\nPress OK to use today ({today}):",
            initialvalue=today,
            parent=root,
        )
        if answer is None:          # user clicked Cancel
            root.destroy()
            return None
        date_str = answer.strip() or today
        try:
            datetime.date.fromisoformat(date_str)
            root.destroy()
            return date_str
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                f"'{date_str}' is not a valid date.\nUse YYYY-MM-DD (e.g. {today}).",
                parent=root,
            )
            root.destroy()
            return None

    def start_review(self, icon=None, item=None):
        _tlog("start_review called")
        if self.is_in_review:
            _tlog("start_review: already in review, ignoring")
            return

        date_str = self._ask_review_date()
        if date_str is None:
            _tlog("start_review: user cancelled date selection")
            return

        _tlog(f"start_review: review date = {date_str}")
        self.review_config = review_engine.load_review_config(self.script_dir)
        review_engine.initialize_review(self.script_dir, date_str=date_str)
        active, state = review_engine.is_review_active(self.script_dir)
        if state is None:
            state = review_engine.load_state()
            _tlog(f"start_review: fallback state load = {state}")
        self.review_state = state
        self.is_in_review = True
        self.update_icon("review")
        self._refresh_menu()
        threading.Thread(target=self._watch_review_completion, daemon=True).start()
        # Kill any stale dashboard windows before opening a fresh one
        try:
            subprocess.run(["pkill", "-f", "review_dashboard.py"], capture_output=True)
        except Exception:
            pass

        # Open the review dashboard window; redirect stderr to log so crashes are visible
        log_path = os.path.join(self.script_dir, "review_debug.log")
        try:
            with open(log_path, "a") as log_fh:
                subprocess.Popen(
                    [sys.executable, os.path.join(self.script_dir, "review_dashboard.py")],
                    close_fds=True,
                    stderr=log_fh,
                    stdout=log_fh,
                )
            _tlog("Dashboard subprocess launched")
        except Exception as e:
            _tlog(f"ERROR launching dashboard: {e}")

    def _load_review_state_or_finish(self):
        """Load current review state; call _review_finished and return None if unavailable."""
        _, state = review_engine.is_review_active(self.script_dir)
        if state is None:
            state = review_engine.load_state()
        if state is None:
            self._review_finished()
            return None
        return state

    def next_step_review(self, icon=None, item=None):
        """Trigger structuring + advance in a background thread so the menu stays responsive."""
        _tlog("next_step_review called")
        if not self.review_config:
            _tlog("next_step_review: no review_config, ignoring")
            return

        state = self._load_review_state_or_finish()
        if state is None:
            _tlog("next_step_review: no state, finishing review")
            return

        if state.get("processing", False):
            _tlog("next_step_review: state[processing]=True, ignoring concurrent click")
            return

        self.review_state = state
        self.update_icon("processing")
        threading.Thread(target=self._structure_and_advance, args=(state,), daemon=True).start()

    def _structure_and_advance(self, _state):
        """Background: delegate to review_engine.structure_and_advance, then update tray UI."""
        # Snapshot config so a concurrent cancel_review() cannot set self.review_config=None
        # and crash this thread mid-execution.
        review_config = self.review_config
        if review_config is None:
            _tlog("_structure_and_advance: review_config gone at thread start, bailing")
            return
        try:
            success, error, still_active = review_engine.structure_and_advance(
                self.script_dir, self.engine, review_config
            )
            _tlog(f"_structure_and_advance: success={success} error={error} still_active={still_active}")
            if error:
                self._notify("Voice Refiner — Error", error[:120])
            if still_active:
                _, new_state = review_engine.is_review_active(self.script_dir)
                self.review_state = new_state
                self.update_icon("review")
            else:
                self._review_finished()
        except Exception as e:
            import traceback
            _tlog(f"EXCEPTION in _structure_and_advance:\n{traceback.format_exc()}")
            self._notify("Voice Refiner — Error", str(e)[:120])
            self.update_icon("review" if self.is_in_review else "idle")
        finally:
            self._refresh_menu()

    def skip_review_step(self, icon=None, item=None):
        _tlog("skip_review_step called")
        if not self.review_config:
            return
        state = self._load_review_state_or_finish()
        if state is None:
            return
        self.review_state = state
        review_engine.skip_step(self.script_dir, self.review_state, self.review_config)
        still_active, new_state = review_engine.is_review_active(self.script_dir)
        if still_active:
            self.review_state = new_state
            self._refresh_menu()
        else:
            self._review_finished()

    def redo_review_step(self, icon=None, item=None):
        _tlog("redo_review_step called")
        if not self.review_config:
            return
        state = self._load_review_state_or_finish()
        if state is None:
            return
        self.review_state = state
        review_engine.redo_step(self.script_dir, self.review_state, self.review_config)
        _, new_state = review_engine.is_review_active(self.script_dir)
        if new_state:
            self.review_state = new_state
        self._refresh_menu()

    def cancel_review(self, icon=None, item=None):
        import traceback
        _tlog(f"cancel_review called from tray. Stack:\n{''.join(traceback.format_stack())}")
        review_engine.cancel_review(self.script_dir)
        self._review_finished()

    def _review_finished(self):
        _tlog("_review_finished called")
        self.is_in_review = False
        self.review_state = None
        self.review_config = None
        self.update_icon("idle")
        self._refresh_menu()

    def _watch_review_completion(self):
        """Daemon thread: detect when the review completes via the dashboard and reset tray state.

        The dashboard process calls review_engine.complete_review() which deletes the state file.
        Without this watcher, the tray never learns the review ended and keeps showing stale
        review menu items indefinitely.  This thread polls every 2 seconds and calls
        _review_finished() as soon as is_review_active() returns False.
        """
        while self.is_in_review and self.running:
            time.sleep(2)
            if not self.is_in_review:
                # Cleared by another path (cancel, tray-driven next-step) — nothing to do
                break
            active, _ = review_engine.is_review_active(self.script_dir)
            if not active:
                _tlog("_watch_review_completion: state gone — review finished externally, resetting tray")
                self._review_finished()
                break

    # ── Normal mode controls ──────────────────────────────────────────────────

    def replay_morning_brief(self, icon=None, item=None):
        import morning_brief as _mb
        state = _mb.load_brief_state()
        if not state:
            return
        text = state.get("text", "")
        if not text:
            return
        cfg = self._get_active_config()
        lang = cfg.get("context_brief_language", "en")
        if lang == "hi":
            intro = f"गुड मॉर्निंग! कल की प्राथमिकताएं:\n{text}"
        else:
            intro = f"Good morning! Here are your priorities for today:\n{text}"
        threading.Thread(target=review_engine.narrate, args=(intro, cfg), daemon=True).start()
        _tlog("replay_morning_brief: narrating")

    def open_gui(self, icon=None, item=None):
        subprocess.Popen([sys.executable, os.path.join(self.script_dir, "main_gui.py")])

    def open_settings(self, icon=None, item=None):
        subprocess.Popen([sys.executable, os.path.join(self.script_dir, "config_gui.py")])

    def cycle_mode(self, icon=None, item=None):
        current = self.engine.config.get("MODE", "refine")
        new_mode = "translate" if current == "refine" else "refine"
        self.engine.config["MODE"] = new_mode
        try:
            # Re-read from disk so we only update MODE without clobbering
            # any settings saved by config_gui.py since the tray started.
            config_path = os.path.join(self.script_dir, "config.json")
            disk_cfg = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    disk_cfg = json.load(f)
            disk_cfg["MODE"] = new_mode
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(disk_cfg, f, indent=4)
        except Exception as e:
            _tlog(f"cycle_mode: error saving config: {e}")
        self._refresh_menu()

    def exit_app(self, icon=None, item=None):
        _tlog("exit_app called")
        self.running = False
        if self._wake_listener:
            self._wake_listener.stop()
        if self.listener:
            self.listener.stop()
        if self.icon:
            self.icon.stop()
        # Force-exit so faster-whisper / background threads don't keep process alive
        import os as _os
        _os._exit(0)

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self):
        signal.signal(signal.SIGINT,  lambda sig, frame: self.exit_app())
        signal.signal(signal.SIGTERM, lambda sig, frame: self.exit_app())
        signal.signal(signal.SIGUSR1, lambda sig, frame: self.toggle_recording())

        try:
            self.listener.start()
            _tlog("Tray application running. Ctrl+Alt+V or SIGUSR1 to record.")
            print("Tray application is running. Use the menu or Ctrl+Alt+V.")
            self.icon.run()
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            self.exit_app()


if __name__ == "__main__":
    app = VoiceAssistantTray()
    app.run()
