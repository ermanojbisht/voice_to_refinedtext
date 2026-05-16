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
import sys
import signal

_LOG_FILE = None

def _tlog(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [tray] {msg}"
    print(line)
    if _LOG_FILE:
        try:
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

# ---- TRAY ICON MANAGER ----

class VoiceAssistantTray:
    def __init__(self):
        global _LOG_FILE
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        _LOG_FILE = os.path.join(self.script_dir, "review_debug.log")
        import review_engine
        review_engine.init_logging(self.script_dir)
        _tlog("=" * 50)
        _tlog("VoiceAssistantTray starting")
        self.engine = VoiceEngine(self.script_dir)

        # Current app states
        self.is_recording = False
        self.is_processing = False
        self.running = True

        # Review state tracking
        self.is_in_review = False
        self.review_config = None
        self.review_state = None

        # Generate initial icons
        self.icons = {
            "idle": self.create_status_icon("#45475a"),      # Gray/Slate
            "recording": self.create_status_icon("#f38ba8"), # Red
            "processing": self.create_status_icon("#89b4fa"),# Blue
            "review": self.create_status_icon("#a6e3a1")     # Green
        }

        # Setup the tray icon with a single static menu that uses dynamic callables
        self.icon = pystray.Icon(
            "AI Voice Refiner",
            self.icons["idle"],
            menu=self._build_static_menu()
        )

        # Hotkey tracking
        self.pressed_keys = set()
        self.hotkey_combo = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('v')}
        self.hotkey_combo_alt = {keyboard.Key.ctrl_r, keyboard.Key.alt_r, keyboard.KeyCode.from_char('v')}

        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

        # Check startup state for resume/expire
        import review_engine
        result, state, cfg = review_engine.check_startup_state(self.script_dir)
        if result == 'resume':
            self.is_in_review = True
            self.review_state = state
            self.review_config = cfg
            self.update_icon("review")
            review_engine.send_step_notification(state, cfg)

    def _build_static_menu(self):
        """Build one static menu with all items; visibility/text are dynamic callables.
        pystray re-evaluates these on every update_menu() call — no menu rebuild needed."""

        def _step_label(item):
            if not self.is_in_review or not self.review_state or not self.review_config:
                return "Review in progress"
            import review_engine
            total = review_engine.get_step_count(self.review_config)
            step = review_engine.get_current_step(self.review_state, self.review_config)
            idx = self.review_state.get("current_step_index", 0)
            if step:
                name = step["section_name"]
                if self.review_state.get("awaiting_more", False):
                    return f"Step {idx+1}/{total}: {name} \u2713 Saved"
                return f"Step {idx+1}/{total}: {name}"
            return "Review in progress"

        def _in_review(item):
            return self.is_in_review

        def _not_in_review(item):
            return not self.is_in_review

        def _awaiting(item):
            return self.is_in_review and bool(self.review_state and self.review_state.get("awaiting_more", False))

        def _not_awaiting(item):
            return self.is_in_review and not bool(self.review_state and self.review_state.get("awaiting_more", False))

        def _mode_label(item):
            return f"Mode: {self.engine.config.get('MODE', 'refine').capitalize()}"

        return pystray.Menu(
            # ── Review mode ──
            pystray.MenuItem(_step_label, None, enabled=False, visible=_in_review),
            pystray.MenuItem("Next Step",      self.next_step_review,  visible=_awaiting),
            pystray.MenuItem("Skip This Step", self.skip_review_step,  visible=_not_awaiting),
            pystray.MenuItem("Redo This Step", self.redo_review_step,  visible=_in_review),
            pystray.MenuItem("Cancel Review",  self.cancel_review,     visible=_in_review),
            pystray.Menu.SEPARATOR,
            # ── Normal mode ──
            pystray.MenuItem("Start Recording",      self.toggle_recording,   visible=_not_in_review),
            pystray.MenuItem(_mode_label,             self.cycle_mode,         visible=_not_in_review),
            pystray.MenuItem("Start Evening Review",  self.start_review,       visible=_not_in_review),
            pystray.MenuItem("Open Dashboard",        self.open_gui,           visible=_not_in_review),
            pystray.MenuItem("Settings",              self.open_settings,      visible=_not_in_review),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.exit_app)
        )

    def on_press(self, key):
        if key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.pressed_keys.add(keyboard.Key.ctrl_l if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl else keyboard.Key.ctrl_r)
        elif key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.pressed_keys.add(keyboard.Key.alt_l if key == keyboard.Key.alt_l or key == keyboard.Key.alt else keyboard.Key.alt_r)
        elif hasattr(key, 'char') and key.char == 'v':
            self.pressed_keys.add(keyboard.KeyCode.from_char('v'))

        # Check if combo is pressed
        if all(k in self.pressed_keys for k in [keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('v')]) or \
           all(k in self.pressed_keys for k in [keyboard.Key.ctrl_r, keyboard.Key.alt_r, keyboard.KeyCode.from_char('v')]):
            self.toggle_recording()

    def on_release(self, key):
        if key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.pressed_keys.discard(keyboard.Key.ctrl_l)
            self.pressed_keys.discard(keyboard.Key.ctrl_r)
        elif key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.pressed_keys.discard(keyboard.Key.alt_l)
            self.pressed_keys.discard(keyboard.Key.alt_r)
        elif hasattr(key, 'char') and key.char == 'v':
            self.pressed_keys.discard(keyboard.KeyCode.from_char('v'))

    def create_status_icon(self, color):
        """Generates a simple 64x64 circle icon for the tray."""
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill=color)
        return image

    def update_icon(self, state):
        """Switches the tray icon image based on current activity."""
        self.icon.icon = self.icons.get(state, self.icons["idle"])

    def toggle_recording(self):
        """The main action triggered by the hotkey or menu."""
        if not self.is_recording and not self.is_processing:
            threading.Thread(target=self.run_full_process, daemon=True).start()
        elif self.is_recording:
            self.engine.stop_recording()

    def _notify(self, title, message):
        """Fire a desktop notification, fallback to print."""
        try:
            subprocess.run(["notify-send", "-i", "dialog-information", "-t", "4000", title, message],
                           timeout=5, check=False)
        except Exception:
            print(f"[{title}] {message}")

    def run_full_process(self):
        """Orchestrates the full Record -> Transcribe -> Refine cycle."""
        import review_engine
        try:
            self.is_recording = True
            self.update_icon("recording")
            _tlog(f"run_full_process started. is_in_review={self.is_in_review}")

            # Send step reminder before recording — only when NOT already awaiting_more
            # (if awaiting_more=True the user knows the step; no need to re-notify)
            if self.is_in_review and self.review_state and self.review_config:
                if not self.review_state.get("awaiting_more", False):
                    review_engine.send_step_notification(self.review_state, self.review_config)

            wav_path = self.engine.record()

            self.is_recording = False
            self.is_processing = True
            self.update_icon("processing")

            # Stage 1: Transcribing
            self._notify("Voice Refiner", "Transcribing audio...")
            raw_text = self.engine.transcribe(wav_path)
            _tlog(f"Transcription done. text_len={len(raw_text)} preview='{raw_text[:80]}'")

            if not raw_text.strip():
                self._notify("Voice Refiner", "No speech detected. Try again.")
                _tlog("No speech detected, returning")
                self.is_processing = False
                self.update_icon("review" if self.is_in_review else "idle")
                return

            # ── PRIMARY ROUTING: use in-memory flag, not disk re-check ──
            if self.is_in_review:
                _tlog("Routing: REVIEW MODE")
                self._handle_review_step(raw_text)
            else:
                _tlog("Routing: NORMAL MODE")
                self._run_normal_mode(raw_text)

            self.is_processing = False
            if self.is_in_review:
                self.update_icon("review")
            else:
                self.update_icon("idle")

        except Exception as e:
            import traceback
            err_detail = traceback.format_exc()
            _tlog(f"EXCEPTION in run_full_process:\n{err_detail}")
            self._notify("Voice Refiner — Error", str(e)[:100])
            self.is_recording = False
            self.is_processing = False
            if self.is_in_review:
                self.update_icon("review")
            else:
                self.update_icon("idle")

    def _handle_review_step(self, raw_text):
        """Handles a single review step: refine, save to Obsidian, advance."""
        import review_engine
        _tlog("_handle_review_step called")

        # Reload state from disk to get latest (e.g. after skip/redo from menu)
        _, fresh_state = review_engine.is_review_active(self.script_dir)
        if fresh_state is None:
            # State file gone (expired or cancelled while recording) — fallback
            _tlog("WARNING: is_in_review=True but state file gone. Falling back to normal mode.")
            self._review_finished()
            self._run_normal_mode(raw_text)
            return

        self.review_state = fresh_state
        step = review_engine.get_current_step(fresh_state, self.review_config)

        if step is None:
            _tlog("ERROR: get_current_step returned None — all steps done or bad state")
            self._notify("Voice Refiner", "Review error: could not get current step.")
            return

        step_name = step.get('section_name', f"Step {fresh_state.get('current_step_index', '?')}")
        is_continuation = fresh_state.get("awaiting_more", False)
        _tlog(f"Current step: '{step_name}' idx={fresh_state.get('current_step_index')} refine={step.get('refine', True)} is_continuation={is_continuation}")

        # Stage 2: Refine or raw
        if step.get('refine', True):
            if is_continuation:
                self._notify("Voice Refiner", f"Refining continuation for '{step_name}'...")
            else:
                self._notify("Voice Refiner", f"Refining text for '{step_name}'...")
            _tlog(f"Calling engine.refine for step '{step_name}'")
            final_text = self.engine.refine(raw_text)
        else:
            _tlog(f"Skipping refinement for step '{step_name}' (refine=False)")
            final_text = raw_text

        _tlog(f"final_text preview: '{final_text[:80]}'")

        # Stage 3: Save to Obsidian (append_to_note uses awaiting_more flag to pick format)
        self._notify("Voice Refiner", f"Saving to '{step_name}'...")
        review_engine.append_to_note(self.script_dir, self.review_config, step, final_text, self.review_state)

        # Mark awaiting_more so the next hotkey appends a continuation
        self.review_state["awaiting_more"] = True
        review_engine._save_state(self.review_state)

        # Notify and update menu — user must click "Next Step" to advance
        if is_continuation:
            self._notify("Voice Refiner", f"More added to '{step_name}'. Speak again or click Next Step.")
        else:
            review_engine.send_awaiting_notification(self.review_state, self.review_config)
        _tlog(f"_handle_review_step: set awaiting_more=True, waiting for user to click Next Step")

        try:
            self.icon.update_menu()
        except Exception as e:
            _tlog(f"_handle_review_step: menu update warning (non-fatal): {e}")

    def _run_normal_mode(self, raw_text):
        """Handles normal mode: refine → clipboard → optional direct typing."""
        _tlog("_run_normal_mode: refining")
        self._notify("Voice Refiner", "Refining text with AI...")
        final_text = self.engine.refine(raw_text)
        self._notify("Voice Refiner", "Done! Text copied to clipboard.")
        _tlog(f"_run_normal_mode: refined, len={len(final_text)}")
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
        if self.engine.config.get("DIRECT_TYPING"):
            self.engine.type_text(final_text)

    def start_review(self, icon=None, item=None):
        import review_engine
        _tlog("start_review called")
        self.review_config = review_engine.load_review_config(self.script_dir)
        review_engine.initialize_review(self.script_dir)
        active, state = review_engine.is_review_active(self.script_dir)
        _tlog(f"start_review: is_review_active={active}, state={state}")
        # Always load state from disk directly as fallback (is_review_active may be strict)
        if state is None:
            state = review_engine._load_state()
            _tlog(f"start_review: fallback state load = {state}")
        self.review_state = state
        self.is_in_review = True
        self.update_icon("review")
        try:
            self.icon.update_menu()
        except Exception as e:
            _tlog(f"start_review: menu update warning (non-fatal): {e}")

    def skip_review_step(self, icon=None, item=None):
        import review_engine
        _tlog("skip_review_step called")
        if not self.review_config:
            _tlog("skip_review_step: no review_config, ignoring")
            return
        # Always reload state from disk for freshness
        _, state = review_engine.is_review_active(self.script_dir)
        if state is None:
            state = review_engine._load_state()
        if state is None:
            _tlog("skip_review_step: no state found, cancelling review")
            self._review_finished()
            return
        self.review_state = state
        review_engine.skip_step(self.script_dir, self.review_state, self.review_config)
        still_active, new_state = review_engine.is_review_active(self.script_dir)
        _tlog(f"skip_review_step: still_active={still_active}")
        if still_active:
            self.review_state = new_state
            try:
                self.icon.update_menu()
            except Exception as e:
                _tlog(f"skip_review_step: menu update warning (non-fatal): {e}")
        else:
            self._review_finished()

    def next_step_review(self, icon=None, item=None):
        import review_engine
        _tlog("next_step_review called")
        if not self.review_config:
            _tlog("next_step_review: no review_config, ignoring")
            return
        # Reload fresh state from disk
        _, state = review_engine.is_review_active(self.script_dir)
        if state is None:
            state = review_engine._load_state()
        if state is None:
            _tlog("next_step_review: no state found, finishing review")
            self._review_finished()
            return
        # Reset awaiting_more then advance
        state["awaiting_more"] = False
        review_engine._save_state(state)
        self.review_state = state
        review_engine.advance_step(self.script_dir, self.review_state, self.review_config)
        still_active, new_state = review_engine.is_review_active(self.script_dir)
        _tlog(f"next_step_review: still_active={still_active}")
        if still_active:
            self.review_state = new_state
            try:
                self.icon.update_menu()
            except Exception as e:
                _tlog(f"next_step_review: menu update warning (non-fatal): {e}")
        else:
            self._review_finished()

    def redo_review_step(self, icon=None, item=None):
        import review_engine
        _tlog("redo_review_step called")
        if not self.review_config:
            _tlog("redo_review_step: no review_config, ignoring")
            return
        # Always reload state from disk for freshness
        _, state = review_engine.is_review_active(self.script_dir)
        if state is None:
            state = review_engine._load_state()
        if state is None:
            _tlog("redo_review_step: no state found, cancelling review")
            self._review_finished()
            return
        self.review_state = state
        if self.review_state and self.review_config:
            review_engine.redo_step(self.script_dir, self.review_state, self.review_config)
            active, new_state = review_engine.is_review_active(self.script_dir)
            _tlog(f"redo_review_step: still_active={active}")
            if active:
                self.review_state = new_state
                try:
                    self.icon.update_menu()
                except Exception as e:
                    _tlog(f"redo_review_step: menu update warning (non-fatal): {e}")

    def cancel_review(self, icon=None, item=None):
        import review_engine
        review_engine.cancel_review(self.script_dir)
        self._review_finished()

    def _review_finished(self):
        _tlog("_review_finished called")
        self.is_in_review = False
        self.review_state = None
        self.review_config = None
        self.update_icon("idle")
        try:
            self.icon.update_menu()
        except Exception as e:
            _tlog(f"_review_finished: menu update warning (non-fatal): {e}")

    def open_gui(self, icon=None, item=None):
        """Launches the main GUI dashboard."""
        subprocess.Popen([sys.executable, os.path.join(self.script_dir, "main_gui.py")])

    def open_settings(self, icon=None, item=None):
        """Launches the settings window."""
        subprocess.Popen([sys.executable, os.path.join(self.script_dir, "config_gui.py")])

    def cycle_mode(self, icon, item):
        """Toggles between Refine and Translate modes."""
        current = self.engine.config.get("MODE", "refine")
        new_mode = "translate" if current == "refine" else "refine"

        self.engine.config["MODE"] = new_mode
        with open(os.path.join(self.script_dir, "config.json"), "w") as f:
            json.dump(self.engine.config, f, indent=4)

        self.icon.update_menu()

    def exit_app(self, icon=None, item=None):
        """Signals the application components to stop."""
        print("Stopping application...")
        self.running = False
        if self.listener:
            self.listener.stop()
        if self.icon:
            self.icon.stop()

    def run(self):
        """Starts the tray icon and the hotkey listener."""
        signal.signal(signal.SIGINT, lambda sig, frame: self.exit_app())
        signal.signal(signal.SIGTERM, lambda sig, frame: self.exit_app())
        signal.signal(signal.SIGUSR1, lambda sig, frame: self.toggle_recording())

        try:
            self.listener.start()
            print("Tray application is running. Use the menu or Ctrl+Alt+V.")
            self.icon.run()
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            self.exit_app()

if __name__ == "__main__":
    app = VoiceAssistantTray()
    app.run()
