"""audio_toolkit/overlay.py.

Floating Minimal Pill Overlay Widget with Real-Time Reactive Waveform Canvas (Track B).
Zero-Focus, Always-On-Top desktop indicator for Linux (Wayland / X11).

Key Characteristics:
1. Zero Focus Stealing:
   - Uses root.overrideredirect(True) and topmost attribute.
   - Never intercepts or steals active window keyboard focus (Word / Terminal remain focused).
2. Dynamic States:
   - Listening (🎙️ Red/Cyan + Live Bouncing Waveform Equalizer)
   - Thinking / Refining (🧠 Lavender pulsing glow)
   - Pasted / Done (✨ Mint Green check + auto-hide after 1.2s)
"""

from __future__ import annotations

import os
import queue
import threading
import time
from typing import Optional

try:
    import tkinter as tk
    _TK_AVAILABLE = True
except ImportError:
    _TK_AVAILABLE = False


class RecordingOverlay:
    """Zero-focus floating pill overlay showing real-time recording and audio waveforms."""

    def __init__(self):
        self._enabled = True
        self._cmd_queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._ready_event = threading.Event()
        self._root = None
        self._canvas = None
        self._icon_label = None
        self._text_label = None
        self._state = "hidden"
        self._position = "top"  # 'top', 'bottom', 'bottom_right'
        self._style = "wave"    # 'wave', 'stagnant', 'hidden'
        self._num_bars = 7
        self._bar_heights = [4.0] * self._num_bars
        self._rms_level = 0.0

        self._load_config()

        if _TK_AVAILABLE and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            self._start_thread()

    def _load_config(self):
        try:
            import json
            cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
            if os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self._position = cfg.get("OVERLAY_POSITION", "top").lower()
                    self._style = cfg.get("OVERLAY_STYLE", "wave").lower()
        except Exception:
            pass

    def _update_geometry(self):
        if not self._root:
            return
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        w, h = 250, 44

        if self._position == "bottom":
            x = (sw - w) // 2
            y = max(30, sh - h - 55)
        elif self._position == "bottom_right":
            x = max(20, sw - w - 30)
            y = max(30, sh - h - 55)
        else:  # 'top'
            x = (sw - w) // 2
            y = 30

        self._root.geometry(f"{w}x{h}+{x}+{y}")

    def _start_thread(self):
        self._thread = threading.Thread(target=self._gui_loop, daemon=True, name="RecordingOverlayGUI")
        self._thread.start()
        self._ready_event.wait(timeout=2.0)

    def _gui_loop(self):
        try:
            self._root = tk.Tk()
            self._root.withdraw()  # Start hidden
            self._root.overrideredirect(True)  # No window decorations, no WM focus stealing
            self._root.attributes("-topmost", True)

            # Dimensions and Position
            self._update_geometry()
            self._root.configure(bg="#181825")  # Catppuccin Crust

            # Container card with border
            card = tk.Frame(
                self._root,
                bg="#1e1e2e",  # Catppuccin Base
                highlightbackground="#313244",  # Surface0 border
                highlightthickness=1,
                padx=12,
                pady=6
            )
            card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

            # Left: State Indicator Icon
            self._icon_label = tk.Label(
                card,
                text="🎙",
                font=("Sans", 14),
                bg="#1e1e2e",
                fg="#f38ba8"  # Red / Coral
            )
            self._icon_label.pack(side=tk.LEFT, padx=(0, 8))

            # Center: Status text
            self._text_label = tk.Label(
                card,
                text="Listening...",
                font=("Sans", 10, "bold"),
                bg="#1e1e2e",
                fg="#cdd6f4"  # Text
            )
            self._text_label.pack(side=tk.LEFT, padx=(0, 10))

            # Right: Live Waveform Canvas (Equalizer bars)
            self._canvas = tk.Canvas(
                card,
                width=70,
                height=26,
                bg="#181825",
                highlightthickness=0
            )
            self._canvas.pack(side=tk.RIGHT, padx=4)

            self._ready_event.set()

            # Schedule periodic queue check and animation tick
            self._root.after(30, self._process_queue)
            self._root.mainloop()
        except Exception:
            self._ready_event.set()

    def _process_queue(self):
        """Processes commands from worker threads on Tkinter main thread."""
        try:
            while not self._cmd_queue.empty():
                cmd, args = self._cmd_queue.get_nowait()
                if cmd == "set_position":
                    self._position = str(args).lower()
                    self._update_geometry()
                elif cmd == "set_style":
                    self._style = str(args).lower()
                elif cmd == "show_listening":
                    self._do_show_listening()
                elif cmd == "update_level":
                    self._do_update_level(args)
                elif cmd == "show_thinking":
                    self._do_show_thinking()
                elif cmd == "show_done":
                    self._do_show_done(args)
                elif cmd == "hide":
                    self._do_hide()
        except Exception:
            pass

        # Animate waveform canvas at ~30 FPS
        if self._state == "listening":
            self._draw_waveform()
        elif self._state == "thinking":
            self._draw_thinking_pulse()

        if self._root:
            self._root.after(33, self._process_queue)

    def _do_show_listening(self):
        if self._style == "hidden":
            return
        self._state = "listening"
        self._update_geometry()
        if self._icon_label:
            self._icon_label.config(text="🎙", fg="#f38ba8")
        if self._text_label:
            self._text_label.config(text="Listening...", fg="#f38ba8")
        if self._root:
            self._root.deiconify()

    def _do_update_level(self, rms: float):
        self._rms_level = max(0.0, float(rms))

    def _do_show_thinking(self):
        if self._style == "hidden":
            return
        self._state = "thinking"
        self._update_geometry()
        if self._icon_label:
            self._icon_label.config(text="🧠", fg="#b4befe")
        if self._text_label:
            self._text_label.config(text="Refining...", fg="#b4befe")
        if self._root:
            self._root.deiconify()

    def _do_show_done(self, message: str = "Pasted!"):
        if self._style == "hidden":
            return
        self._state = "done"
        if self._icon_label:
            self._icon_label.config(text="✨", fg="#a6e3a1")
        if self._text_label:
            self._text_label.config(text=message, fg="#a6e3a1")
        if self._canvas:
            self._canvas.delete("all")
        if self._root:
            self._root.deiconify()
            # Auto-hide after 1.2s
            self._root.after(1200, self._do_hide)

    def _do_hide(self):
        self._state = "hidden"
        if self._root:
            self._root.withdraw()

    def _draw_waveform(self):
        if not self._canvas:
            return
        self._canvas.delete("all")
        cw = 70
        ch = 26
        bar_w = 6
        gap = 4

        # Stagnant / Minimal mode: calm, steady indicator without moving bars
        if self._style == "stagnant":
            for i in range(self._num_bars):
                bh = 8.0
                x1 = i * (bar_w + gap) + 4
                x2 = x1 + bar_w
                y1 = (ch - bh) / 2.0
                y2 = y1 + bh
                self._canvas.create_rectangle(x1, y1, x2, y2, fill="#89b4fa", width=0)
            return

        # Dynamic Wave mode: bouncing to speech RMS
        target_norm = min(1.0, max(0.1, self._rms_level / 800.0))
        import random
        for i in range(self._num_bars):
            curve_factor = 1.0 - (abs(i - 3) / 4.0) * 0.4
            target_h = max(3.0, target_norm * 22.0 * curve_factor * (0.8 + 0.4 * random.random()))
            self._bar_heights[i] = self._bar_heights[i] * 0.5 + target_h * 0.5
            bh = self._bar_heights[i]
            x1 = i * (bar_w + gap) + 4
            x2 = x1 + bar_w
            y1 = (ch - bh) / 2.0
            y2 = y1 + bh
            color = "#89b4fa" if i % 2 == 0 else "#a6e3a1"
            self._canvas.create_rectangle(x1, y1, x2, y2, fill=color, width=0)

    def _draw_thinking_pulse(self):
        if not self._canvas:
            return
        self._canvas.delete("all")
        # Gentle scanning pulse
        cw = 70
        ch = 26
        t = time.time() * 4.0
        for i in range(self._num_bars):
            phase = (t + i * 0.5) % 3.14159
            bh = 4.0 + 16.0 * max(0.0, float(abs(phase - 1.57) < 1.0) * (1.0 - abs(phase - 1.57)))
            x1 = i * (6 + 4) + 4
            x2 = x1 + 6
            y1 = (ch - bh) / 2.0
            y2 = y1 + bh
            self._canvas.create_rectangle(x1, y1, x2, y2, fill="#b4befe", width=0)

    # ── Thread-Safe Public API ───────────────────────────────────────────────

    def show_listening(self):
        """Displays overlay in Listening state."""
        self._cmd_queue.put(("show_listening", None))

    def update_level(self, rms: float):
        """Updates live audio RMS level for real-time waveform bars."""
        self._cmd_queue.put(("update_level", rms))

    def show_thinking(self):
        """Displays overlay in Thinking / Refining state."""
        self._cmd_queue.put(("show_thinking", None))

    def show_done(self, message: str = "Pasted!"):
        """Displays overlay in Done state, auto-hiding after 1.2s."""
        self._cmd_queue.put(("show_done", message))

    def set_position(self, pos: str):
        """Sets overlay screen position: 'top', 'bottom', or 'bottom_right'."""
        self._cmd_queue.put(("set_position", pos))

    def set_style(self, style: str):
        """Sets overlay animation style: 'wave', 'stagnant', or 'hidden'."""
        self._cmd_queue.put(("set_style", style))

    def hide(self):
        """Immediately hides overlay."""
        self._cmd_queue.put(("hide", None))


# Singleton instance
_overlay_instance: Optional[RecordingOverlay] = None


def get_recording_overlay() -> RecordingOverlay:
    """Return the global RecordingOverlay singleton."""
    global _overlay_instance
    if _overlay_instance is None:
        _overlay_instance = RecordingOverlay()
    return _overlay_instance
