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
import math

import utils as _utils
utils = _utils

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
        self._auto_advance_timer = None   # fires after silence to auto-advance step

        # Icons: crisp vector sets with animation frame sequences
        self.icon_frames = {
            "idle":       [self.create_status_icon("idle")],
            "recording":  [self.create_status_icon("recording", f) for f in range(4)],
            "processing": [self.create_status_icon("processing", f) for f in range(4)],
            "review":     [self.create_status_icon("review")],
        }
        self.icons = {
            "idle":       self.icon_frames["idle"][0],
            "recording":  self.icon_frames["recording"][0],
            "processing": self.icon_frames["processing"][0],
            "review":     self.icon_frames["review"][0],
        }
        self._current_icon_state = "idle"
        self._icon_anim_running = False

        # Setup hotkey configuration from config.json
        self._setup_hotkey()

        # Build tray icon with single static menu (dynamic callables)
        active_prof = self.engine.config.get("ACTIVE_MODEL_PROFILE") or self.engine.config.get("ASR_ENGINE") or "whisper"
        self.icon = pystray.Icon(
            "AI Voice Refiner",
            self.icons["idle"],
            title=f"AI Voice Refiner ({active_prof})",
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

        # Start lightweight local settings server daemon (127.0.0.1:8765)
        try:
            import settings_server
            settings_server.start_server_daemon()
        except Exception as e:
            _tlog(f"Settings server daemon notice: {e}")

        # Live config file watcher: synchronizes changes made via Web Settings or Dashboard immediately
        self._last_config_mtime = self._get_config_mtime()
        self._start_config_watcher()

        # Eager non-blocking background pre-warming (Vulkan shader compile + Ollama warm-up)
        threading.Thread(target=self._background_prewarm, daemon=True, name="prewarm").start()

    def _get_config_mtime(self) -> float:
        cfg_path = os.path.join(self.script_dir, "config.json")
        try:
            return os.path.getmtime(cfg_path) if os.path.exists(cfg_path) else 0.0
        except OSError:
            return 0.0

    def _setup_hotkey(self):
        """Loads and parses the global hotkey from config.json."""
        raw_hk = self.engine.config.get("GLOBAL_HOTKEY", "Ctrl+Space")
        self.hotkey_display = utils.format_hotkey_display(raw_hk)
        self.hotkey_modifiers, self.hotkey_trigger = utils.parse_hotkey(raw_hk)
        _tlog(f"Global hotkey configured: {self.hotkey_display}")

    def _sync_config_from_disk(self):
        """Checks if config.json changed on disk and reloads it, updating title and menu."""
        current_mtime = self._get_config_mtime()
        if current_mtime != self._last_config_mtime and current_mtime > 0:
            self._last_config_mtime = current_mtime
            _tlog(f"config.json modification detected on disk (mtime={current_mtime}) — updating tray app")
            self.engine.reload_config()
            self._setup_hotkey()
            self._update_tray_title()
            self._refresh_menu()
            try:
                from audio_toolkit import get_recording_overlay
                ov = get_recording_overlay()
                ov.set_position(self.engine.config.get("OVERLAY_POSITION", "top"))
                ov.set_style(self.engine.config.get("OVERLAY_STYLE", "wave"))
            except Exception:
                pass

    def _start_config_watcher(self):
        """Periodically checks config.json mtime in background to auto-sync web changes."""
        def watch_loop():
            while self.running:
                time.sleep(1.0)
                try:
                    self._sync_config_from_disk()
                except Exception as exc:
                    _tlog(f"config watcher notice: {exc}")

        threading.Thread(target=watch_loop, daemon=True, name="config_watcher").start()

    def _get_active_config(self):
        """Return the current review config — live session config if active, else reload from disk."""
        return self.review_config or review_engine.load_review_config(self.script_dir)

    def _background_prewarm(self):
        """Pre-compiles Vulkan shaders and warms up Ollama LLM in the background.

        Eliminates the ~33s cold start delay on the first audio recording without
        blocking the tray application launch.
        """
        _tlog("Background pre-warm started")
        try:
            # 1. Warm up active ASR provider (loads weights and compiles Vulkan shaders)
            if self.engine and hasattr(self.engine, "asr_provider"):
                import numpy as _np
                dummy_pcm = _np.zeros(1600, dtype=_np.float32)  # 0.1s silence
                t0 = time.time()
                self.engine.asr_provider.transcribe(dummy_pcm)
                dt = (time.time() - t0) * 1000
                _tlog(f"Background pre-warm: ASR ready ({dt:.1f}ms, shaders cached)")

            # 2. Warm up Ollama LLM if keep_alive is configured (not '0')
            keep_alive = self.engine.config.get("OLLAMA_KEEP_ALIVE", "5m")
            if str(keep_alive).strip().lower() not in {"0", "0s", "none"}:
                host = self.engine.config.get("OLLAMA_HOST", "http://localhost:11434")
                model = self.engine.config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")
                t0 = time.time()
                _utils.call_ollama(host, model, "hi", stop_tokens=[], keep_alive=keep_alive)
                dt = (time.time() - t0) * 1000
                _tlog(f"Background pre-warm: Ollama '{model}' ready in VRAM ({dt:.1f}ms, keep_alive={keep_alive})")
            else:
                _tlog("Background pre-warm: Ollama warm-up skipped (OLLAMA_KEEP_ALIVE=0 for low VRAM)")
        except Exception as exc:
            _tlog(f"Background pre-warm notice: {exc}")

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
                back_fn=lambda: self.redo_review_step() if self.is_in_review else None,
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
        def _preset_label(item):
            self._sync_config_from_disk()
            cur = self.engine.get_active_preset()
            presets = self.engine.config.get("ASR_PRESETS", {})
            lbl = presets.get(cur, {}).get("label", cur)
            return f"🎙 Preset: {lbl}"

        def _goal_label(item):
            self._sync_config_from_disk()
            cur = self.engine.get_active_goal()
            goals = self.engine.config.get("REFINEMENT_GOALS", {})
            lbl = goals.get(cur, {}).get("label", cur)
            return f"✨ Goal: {lbl}"

        def _has_morning_brief(item):
            import morning_brief as _mb
            return not self.is_in_review and _mb.load_brief_state() is not None
        def _start_review_visible(item):
            return not self.is_in_review and _evening_review_enabled(item)
        def _record_label(item):
            return f"Start Recording ({self.hotkey_display})"

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
            pystray.MenuItem("🔁 Re-process Last Audio", self.reprocess_last_audio,         visible=_not_in_review),
            pystray.MenuItem(_preset_label,            self.cycle_preset,                   visible=_not_in_review),
            pystray.MenuItem(_goal_label,              self.cycle_goal,                     visible=_not_in_review),
            pystray.MenuItem("Start Evening Review",   self.start_review,                   visible=_start_review_visible),
            pystray.MenuItem("🌅 Replay Morning Brief", self.replay_morning_brief,          visible=_has_morning_brief),
            pystray.MenuItem("Open Dashboard",         self.open_gui,                       visible=_not_in_review),
            pystray.MenuItem("🏛 PWD Terminology Lookup", self.open_pwd_lookup,               visible=_not_in_review),
            pystray.MenuItem("Audio to Ideas",          self.open_audio_to_idea,              visible=self._audio_to_idea_enabled),
            pystray.MenuItem("Settings",               self.open_settings,                  visible=_not_in_review),
            pystray.MenuItem("📖 User Manual & Help",   self.open_user_manual,               visible=_not_in_review),
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
        if utils.is_modifier_key(key):
            self.pressed_keys.add(key)
            return

        # 1. Narration hotkeys: Ctrl+Alt+S (stop) and Ctrl+Alt+R (replay)
        if hasattr(key, "char") and key.char in ("s", "r") and self._ctrl() and self._alt():
            if key.char == "s":
                threading.Thread(target=review_engine.stop_narration, daemon=True).start()
                return
            elif key.char == "r":
                threading.Thread(target=review_engine.replay_narration,
                                 args=(self._get_active_config(),), daemon=True).start()
                return

        # 2. Configurable Global Recording Hotkey
        if utils.matches_hotkey(self.pressed_keys, key, self.hotkey_modifiers, self.hotkey_trigger):
            self.toggle_recording()

    def on_release(self, key):
        self.pressed_keys.discard(key)

    # ── Icon helpers ──────────────────────────────────────────────────────────

    def create_status_icon(self, mode_or_color, frame=0):
        """Creates a crisp 64x64 RGBA vector icon for the system tray (Mic, Ear, Brain, Moon)."""
        if isinstance(mode_or_color, str) and mode_or_color.startswith("#"):
            color_map = {
                "#45475a": "idle",
                "#f38ba8": "recording",
                "#89b4fa": "processing",
                "#a6e3a1": "review",
            }
            mode = color_map.get(mode_or_color, "idle")
        else:
            mode = mode_or_color

        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base pill container with subtle border
        draw.rounded_rectangle((4, 4, 60, 60), radius=16, fill="#1e1e2e", outline="#363a4f", width=2)

        if mode == "idle":
            # 🎙 Crisp Microphone
            col = "#cdd6f4"
            draw.rounded_rectangle((27, 16, 37, 34), radius=5, fill=col)
            draw.arc((21, 22, 43, 40), start=0, end=180, fill=col, width=3)
            draw.line((32, 40, 32, 47), fill=col, width=3)
            draw.line((25, 47, 39, 47), fill=col, width=3)

        elif mode == "recording":
            # 👂 Listening Ear with dynamic radiating acoustic waves
            col = "#f38ba8"
            draw.arc((14, 18, 32, 46), start=70, end=290, fill=col, width=3)
            draw.arc((18, 24, 28, 38), start=80, end=280, fill=col, width=2)
            waves = [(30, 22, 42, 42), (36, 16, 50, 48), (42, 10, 58, 54)]
            active_count = 1 + (frame % 3)
            for i in range(active_count):
                draw.arc(waves[i], start=-55, end=55, fill=col, width=3)

        elif mode == "processing":
            # 🧠 Neural Brain with orbiting synaptic spark
            col = "#89b4fa"
            draw.ellipse((16, 20, 32, 44), outline=col, width=2)
            draw.ellipse((32, 20, 48, 44), outline=col, width=2)
            draw.line((32, 22, 32, 42), fill="#363a4f", width=2)
            angle = (frame * (math.pi / 2))
            sx = int(32 + 20 * math.cos(angle))
            sy = int(32 + 13 * math.sin(angle))
            draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill="#f9e2af")

        elif mode == "review":
            # 🌙 Crescent Moon
            col = "#a6e3a1"
            draw.ellipse((18, 16, 46, 44), fill=col)
            draw.ellipse((26, 14, 52, 42), fill="#1e1e2e")

        return img

    def update_icon(self, state_name):
        self._current_icon_state = state_name
        frames = self.icon_frames.get(state_name, self.icon_frames["idle"])
        try:
            self.icon.icon = frames[0]
        except Exception as e:
            _tlog(f"update_icon error: {e}")

        # Launch background frame cycler for animated states if not already running
        if len(frames) > 1 and not getattr(self, "_icon_anim_running", False):
            self._icon_anim_running = True
            threading.Thread(target=self._icon_animation_loop, daemon=True, name="tray_anim").start()

    def _icon_animation_loop(self):
        """Gentle 5 FPS animation loop cycling tray icon frames during recording and processing."""
        frame_idx = 0
        try:
            while getattr(self, "_icon_anim_running", False):
                state = getattr(self, "_current_icon_state", "idle")
                frames = self.icon_frames.get(state, [])
                if len(frames) <= 1:
                    break
                frame_idx = (frame_idx + 1) % len(frames)
                try:
                    self.icon.icon = frames[frame_idx]
                except Exception:
                    break
                time.sleep(0.2)  # 5 FPS
        finally:
            self._icon_anim_running = False

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

    def _notify(self, title, message, icon="dialog-information", urgency="normal", timeout=4000):
        try:
            subprocess.run(
                ["notify-send", "-u", urgency, "-i", icon, "-t", str(timeout), title, message],
                timeout=5, check=False
            )
        except Exception:
            print(f"[{title}] {message}")

    def run_full_process(self):
        """Record → Transcribe → route to review accumulation or normal clipboard."""
        overlay = None
        try:
            try:
                from audio_toolkit import get_recording_overlay
                overlay = get_recording_overlay()
                overlay.set_position(self.engine.config.get("OVERLAY_POSITION", "top"))
                overlay.set_style(self.engine.config.get("OVERLAY_STYLE", "wave"))
                overlay.show_listening()
            except Exception:
                pass

            self.is_recording = True
            self.update_icon("recording")
            _tlog(f"run_full_process started. is_in_review={self.is_in_review}")

            t0 = time.monotonic()
            chunk_cb = (lambda chunk, rms: overlay.update_level(rms)) if overlay else None
            wav_path = self.engine.record(on_audio_chunk=chunk_cb)
            self._last_record_duration = time.monotonic() - t0

            self.is_recording = False

            # Audio quality gate — reject recordings that are too quiet to transcribe
            if not self._check_audio_quality(wav_path):
                self.update_icon("review" if self.is_in_review else "idle")
                if overlay:
                    overlay.hide()
                return

            self.update_icon("processing")
            if overlay:
                overlay.show_thinking()

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
                if overlay:
                    overlay.hide()
                return

            if self.is_in_review:
                _tlog("Routing: REVIEW MODE")
                self._handle_review_step(raw_text)
            else:
                _tlog("Routing: NORMAL MODE")
                self._run_normal_mode(raw_text)

            self.update_icon("review" if self.is_in_review else "idle")

        except Exception as e:
            if overlay:
                try:
                    overlay.hide()
                except Exception:
                    pass
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

        # Log each clip to review_log.json (mirrors log.json for normal mode)
        review_engine._log_review(self.script_dir, {
            "session_date": self.review_state.get("review_date", ""),
            "step_id":      step.get("step_id", ""),
            "step_name":    step_name,
            "clip_number":  clip_count,
            "event":        "clip_recorded",
            "raw_text":     raw_text,
        })

        review_engine.send_awaiting_notification(self.review_state, self.review_config)
        self._refresh_menu()

        # Prompt the user to add more or move on.
        # Use Hindi when configured; mention voice keywords only when voice_control is on.
        voice_on = self.review_config.get("voice_control", False) if self.review_config else False
        lang     = (self.review_config or {}).get("context_brief_language", "en")
        if lang == "hi":
            prompt_text = (
                "नोट हो गया। कुछ और जोड़ना है? 'आगे' बोलें या 'Next Step' दबाएं।"
                if voice_on else
                "नोट हो गया। और बोलना हो तो बोलें, या 'Next Step' दबाएं।"
            )
        else:
            prompt_text = (
                "Noted. Anything to add? Say 'next' to continue."
                if voice_on else
                "Noted. Record more, or click Next Step when ready."
            )
        review_engine.narrate(prompt_text, self.review_config, blocking=False)

        # Auto-advance timer only runs in voice-control mode.
        # In click-driven mode the user explicitly clicks Next Step.
        if voice_on:
            self._reset_auto_advance_timer()

    def _cancel_auto_advance_timer(self):
        """Cancel any pending auto-advance timer."""
        if self._auto_advance_timer is not None:
            self._auto_advance_timer.cancel()
            self._auto_advance_timer = None

    def _reset_auto_advance_timer(self):
        """Cancel existing timer and start a fresh 10-second countdown.

        When the timer fires it narrates a brief prompt then calls next_step_review(),
        exactly as if the user had said 'next'. Cancelled if the user records another clip,
        presses Next Step, skips, or redoes the step.
        """
        self._cancel_auto_advance_timer()

        def _fire():
            if not self.is_in_review:
                return
            # If TTS is still speaking, postpone to avoid intermingling.
            if review_engine.is_narrating():
                _tlog("auto-advance timer: narration active — postponing 5s")
                self._auto_advance_timer = threading.Timer(5.0, _fire)
                self._auto_advance_timer.daemon = True
                self._auto_advance_timer.start()
                return
            _tlog("auto-advance timer fired")
            review_engine.narrate(
                "ठीक है, अगले सवाल पर चलते हैं। / Moving to the next question.",
                self.review_config,
                blocking=True,
            )
            self.next_step_review()

        self._auto_advance_timer = threading.Timer(10.0, _fire)
        self._auto_advance_timer.daemon = True
        self._auto_advance_timer.start()

    def _run_normal_mode(self, raw_text):
        """Normal mode: refine → clipboard → optional direct typing."""
        _tlog("_run_normal_mode: refining")
        self._notify("Voice Refiner", "Refining text with AI...")
        final_text = self.engine.refine(raw_text)

        sug = getattr(self.engine, "last_acoustic_suggestion", None)
        if sug and sug.get("is_mismatch"):
            is_warn = sug.get("severity") == "warning"
            icon = "dialog-warning" if is_warn else "dialog-information"
            urgency = "critical" if is_warn else "normal"
            title = "⚠️ Language Advisory" if not is_warn else "⚠️ Language Mismatch Warning"
            msg = f"{sug.get('title')}: Suggested preset is '{sug.get('suggested_preset')}'.\n(Result copied to clipboard)"
            self._notify(title, msg, icon=icon, urgency=urgency, timeout=8000)
        else:
            self._notify("Voice Refiner", "Done! Text copied to clipboard.")

        _tlog(f"_run_normal_mode: refined, len={len(final_text)}")
        features = self.engine.config.get("FEATURES", {})
        paste_method = self.engine.config.get("PASTE_METHOD")
        is_restore_mode = (features.get("direct_typing", False) and paste_method == "clipboard_restore")
        if features.get("clipboard_output", True) and not is_restore_mode:
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
            try:
                from audio_toolkit import get_recording_overlay
                get_recording_overlay().show_done("Pasted!")
            except Exception:
                pass
        else:
            try:
                from audio_toolkit import get_recording_overlay
                get_recording_overlay().show_done("Copied!")
            except Exception:
                pass

        # Sync to Web Dashboard in real-time
        try:
            from refiner_service import RefinerService
            RefinerService.get_instance().record_external_clip(
                raw_text=raw_text,
                final_text=final_text,
                duration=getattr(self, "_last_record_duration", 0.0),
                preset=self.engine.get_active_preset(),
                goal=self.engine.get_active_goal(),
                acoustic_suggestion=sug,
                acoustic_info=getattr(self.engine, "last_acoustic_info", None)
            )
        except Exception:
            pass

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

        # Open the Executive Review Web Studio with fallback to review_dashboard.py
        try:
            import review_launcher
            review_launcher.launch_review_app(date_str=date_str)
            _tlog("Executive Review Web Studio launched")
        except Exception as e:
            _tlog(f"review_launcher failed ({e}); falling back to review_dashboard.py")
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
            except Exception as e2:
                _tlog(f"ERROR launching dashboard: {e2}")

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
        self._cancel_auto_advance_timer()
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
        self._cancel_auto_advance_timer()
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
        self._cancel_auto_advance_timer()
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
        self._cancel_auto_advance_timer()
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
        try:
            import dashboard_launcher
            dashboard_launcher.launch_dashboard_app()
        except Exception:
            subprocess.Popen([sys.executable, os.path.join(self.script_dir, "main_gui.py")])

    def open_pwd_lookup(self, icon=None, item=None):
        """Launches the dedicated PWD Terminology & SOR Lookup app."""
        try:
            import pwd_lookup_launcher
            pwd_lookup_launcher.launch_pwd_lookup_app()
        except Exception:
            subprocess.Popen([sys.executable, os.path.join(self.script_dir, "main_gui.py")])

    def _audio_to_idea_enabled(self, item=None):
        """Read only the optional module setting; keep tray startup model-free."""
        try:
            from audio_to_idea.config import load_settings
            return load_settings().data["integration"]["enabled"]
        except Exception:
            return False

    def open_audio_to_idea(self, icon=None, item=None):
        """Use the tray interpreter and repo cwd even when launched by GNOME."""
        subprocess.Popen([sys.executable, "-m", "audio_to_idea", "gui"], cwd=self.script_dir)

    def open_settings(self, icon=None, item=None):
        try:
            import config_web_launcher
            config_web_launcher.launch_settings_app()
        except Exception:
            subprocess.Popen([sys.executable, os.path.join(self.script_dir, "config_gui.py")])

    def open_user_manual(self, icon=None, item=None):
        try:
            from manual_service import manual_service
            manual_service.open_in_browser()
        except Exception as e:
            subprocess.Popen([sys.executable, os.path.join(self.script_dir, "manual_gui.py")])

    def reprocess_last_audio(self, icon=None, item=None):
        if self.is_recording:
            self._notify("Audio Refiner", "Cannot re-process while recording")
            return
        def worker():
            self.update_icon("processing")
            active_p = self.engine.get_active_preset()
            active_g = self.engine.get_active_goal()
            self._notify("Audio Refiner", f"🔁 Re-processing last audio ({active_p} / {active_g})...")
            try:
                from refiner_service import RefinerService
                ref_svc = RefinerService.get_instance()
                ref_svc.engine = self.engine
                res = ref_svc.reprocess_last_sync(preset=active_p, goal=active_g)
                if res.get("ok"):
                    txt = res.get("final_text") or res.get("text", "")
                    preview = txt[:90] + ("..." if len(txt) > 90 else "")
                    self._notify("Audio Refiner", f"✨ Re-processed & Copied to Clipboard:\n{preview}")
                else:
                    self._notify("Audio Refiner", f"Error: {res.get('error', 'Failed')}")
            except Exception as exc:
                self._notify("Audio Refiner", f"Failed: {exc}")
            finally:
                self.update_icon("idle")
        threading.Thread(target=worker, daemon=True).start()

    def cycle_preset(self, icon=None, item=None):
        """Cycles to the next configured ASR preset."""
        presets = list(self.engine.config.get("ASR_PRESETS", {}).keys())
        if not presets:
            presets = ["smart_bilingual", "instant_english", "instant_hindi", "roman_hinglish"]
        cur = self.engine.get_active_preset()
        next_p = presets[(presets.index(cur) + 1) % len(presets)] if cur in presets else presets[0]
        self.engine.set_active_preset(next_p)

        cfg_path = os.path.join(self.script_dir, "config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                disk_cfg = json.load(f)
            disk_cfg["ACTIVE_ASR_PRESET"] = next_p
            disk_cfg["ACTIVE_MODEL_PROFILE"] = next_p
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(disk_cfg, f, indent=4, ensure_ascii=False)
            self.engine.reload_config()
        except Exception as e:
            _tlog(f"cycle_preset: error saving config: {e}")

        info = self.engine.config.get("ASR_PRESETS", {}).get(next_p, {})
        self._notify("🎙 Preset Changed", f"{info.get('label', next_p)}\n{info.get('description', '')}")
        self._update_tray_title()
        self._refresh_menu()

    def cycle_goal(self, icon=None, item=None):
        """Cycles to the next configured Refinement Goal."""
        goals = list(self.engine.config.get("REFINEMENT_GOALS", {}).keys())
        if not goals:
            goals = ["clean_bilingual", "official_english", "official_hindi", "concise_summary", "ideas_actions", "roman_hinglish"]
        cur = self.engine.get_active_goal()
        next_g = goals[(goals.index(cur) + 1) % len(goals)] if cur in goals else goals[0]
        self.engine.set_active_goal(next_g)

        info = self.engine.config.get("REFINEMENT_GOALS", {}).get(next_g, {})
        cfg_path = os.path.join(self.script_dir, "config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                disk_cfg = json.load(f)
            disk_cfg["ACTIVE_REFINEMENT_GOAL"] = next_g
            disk_cfg["LANGUAGE_MODE"] = info.get("output_lang", "bilingual")
            disk_cfg["MODE"] = "translate" if info.get("translate") else "refine"
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(disk_cfg, f, indent=4, ensure_ascii=False)
            self.engine.reload_config()
        except Exception as e:
            _tlog(f"cycle_goal: error saving config: {e}")

        self._notify("✨ Goal Changed", f"{info.get('label', next_g)}\n{info.get('description', '')}")
        self._refresh_menu()

    def _update_tray_title(self):
        cur = self.engine.get_active_preset()
        presets = self.engine.config.get("ASR_PRESETS", {})
        lbl = presets.get(cur, {}).get("label", cur)
        if self.icon:
            self.icon.title = f"AI Voice Refiner ({lbl})"

    # Aliases for backward compatibility
    cycle_mode = cycle_goal
    cycle_asr_profile = cycle_preset

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
            _tlog(f"Tray application running. {self.hotkey_display} or SIGUSR1 to record.")
            print(f"Tray application is running. Use the menu or {self.hotkey_display}.")
            self.icon.run()
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            self.exit_app()


if __name__ == "__main__":
    app = VoiceAssistantTray()
    app.run()
