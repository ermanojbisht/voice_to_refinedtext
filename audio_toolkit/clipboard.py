"""audio_toolkit/clipboard.py.

Enterprise-grade, high-reliability Clipboard Save & Restore Auto-Pasting engine
supporting Ubuntu 22.04 through 26.04 under both Wayland and X11.

Inspired by Handy's clipboard.rs architecture:
1. Reads and saves current clipboard contents.
2. Writes refined text to clipboard.
3. Injects paste key combo (Ctrl+V, Ctrl+Shift+V, or Shift+Insert) via:
   - Tier 1: Linux kernel uinput via ydotool raw keycodes (universal Wayland & X11)
   - Tier 2: X11 / XWayland xdotool
   - Tier 3: Python pynput software fallback
4. Holds quiet period (150ms) for target application event queue.
5. Restores original clipboard contents so user clipboard history remains intact.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Optional

try:
    from pynput.keyboard import Controller, Key
    _PYNPUT_AVAILABLE = True
except ImportError:
    _PYNPUT_AVAILABLE = False


def is_wayland() -> bool:
    """Return True if the current desktop session is Wayland."""
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    return session_type == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def is_tool_available(tool_name: str) -> bool:
    """Check if an executable is in PATH."""
    return shutil.which(tool_name) is not None


class ClipboardManager:
    """Manages clipboard read, write, key chord injection, and safe restore."""

    def __init__(self):
        self._keyboard = Controller() if _PYNPUT_AVAILABLE else None

    # ── Clipboard I/O ────────────────────────────────────────────────────────

    def read_text(self) -> Optional[str]:
        """Read current text from system clipboard without crashing."""
        if is_wayland() and is_tool_available("wl-paste"):
            try:
                proc = subprocess.run(
                    ["wl-paste", "--no-newline"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1.0,
                    check=False
                )
                if proc.returncode == 0:
                    return proc.stdout
            except Exception:
                pass

        # X11 or fallback tools
        if is_tool_available("xclip"):
            try:
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1.0,
                    check=False
                )
                if proc.returncode == 0:
                    return proc.stdout
            except Exception:
                pass

        if is_tool_available("xsel"):
            try:
                proc = subprocess.run(
                    ["xsel", "--clipboard", "--output"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1.0,
                    check=False
                )
                if proc.returncode == 0:
                    return proc.stdout
            except Exception:
                pass

        # Python pyperclip fallback
        try:
            import pyperclip
            return pyperclip.paste()
        except Exception:
            return None

    def read_primary_text(self) -> Optional[str]:
        """Read current text from Linux PRIMARY selection (mouse highlight selection)."""
        if is_wayland() and is_tool_available("wl-paste"):
            try:
                proc = subprocess.run(
                    ["wl-paste", "--primary", "--no-newline"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1.0,
                    check=False
                )
                if proc.returncode == 0:
                    return proc.stdout
            except Exception:
                pass

        if is_tool_available("xclip"):
            try:
                proc = subprocess.run(
                    ["xclip", "-selection", "primary", "-o"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1.0,
                    check=False
                )
                if proc.returncode == 0:
                    return proc.stdout
            except Exception:
                pass

        return None

    def write_primary_text(self, text: str) -> bool:
        """Write text to Linux PRIMARY selection (used by terminals on Shift+Insert)."""
        if text is None:
            return False

        if is_wayland() and is_tool_available("wl-copy"):
            try:
                proc = subprocess.run(
                    ["wl-copy", "--primary", "--", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                    check=False
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        if is_tool_available("xclip"):
            try:
                proc = subprocess.run(
                    ["xclip", "-selection", "primary"],
                    input=text.encode("utf-8"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                    check=False
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        return False

    def write_text(self, text: str) -> bool:
        """Write text to system clipboard.

        On Wayland, uses wl-copy with detached stdout/stderr to avoid hanging
        on background daemon file descriptors.
        """
        if text is None:
            return False

        if is_wayland() and is_tool_available("wl-copy"):
            try:
                proc = subprocess.run(
                    ["wl-copy", "--", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                    check=False
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        # X11 xclip
        if is_tool_available("xclip"):
            try:
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                    check=False
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        # X11 xsel
        if is_tool_available("xsel"):
            try:
                proc = subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode("utf-8"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                    check=False
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        # Python pyperclip
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    def clear(self) -> bool:
        """Clear clipboard content."""
        if is_wayland() and is_tool_available("wl-copy"):
            try:
                subprocess.run(["wl-copy", "--clear"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                return True
            except Exception:
                pass
        return self.write_text("")

    # ── Key Chord Injection ──────────────────────────────────────────────────

    def inject_paste_chord(self, key_combo: str = "ctrl_v") -> bool:
        """Inject paste key combo into currently active window.

        Tiers:
        1. ydotool raw keycodes (Linux kernel uinput - works on Wayland & X11)
        2. xdotool (X11 / XWayland)
        3. pynput (Python Xlib controller)
        """
        key_combo = key_combo.lower().replace("-", "_").replace("+", "_")

        # Tier 1: ydotool raw keycodes
        # Keycodes from <linux/input-event-codes.h>:
        # KEY_LEFTCTRL = 29, KEY_LEFTSHIFT = 42, KEY_V = 47, KEY_INSERT = 110
        if is_tool_available("ydotool"):
            raw_codes = {
                "ctrl_v": ["29:1", "47:1", "47:0", "29:0"],
                "ctrl_shift_v": ["29:1", "42:1", "47:1", "47:0", "42:0", "29:0"],
                "shift_insert": ["42:1", "110:1", "110:0", "42:0"],
            }.get(key_combo, ["42:1", "110:1", "110:0", "42:0"])

            try:
                proc = subprocess.run(
                    ["ydotool", "key", "-d", "20"] + raw_codes,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.5,
                    check=False
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        # Tier 2: xdotool (on X11 or XWayland fallback)
        if is_tool_available("xdotool"):
            xdotool_arg = {
                "ctrl_v": "ctrl+v",
                "ctrl_shift_v": "ctrl+shift+v",
                "shift_insert": "shift+Insert",
            }.get(key_combo, "ctrl+v")

            try:
                proc = subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", xdotool_arg],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.5,
                    check=False
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        # Tier 3: pynput keyboard controller
        if self._keyboard is not None:
            try:
                if key_combo == "shift_insert":
                    with self._keyboard.pressed(Key.shift):
                        self._keyboard.press(Key.insert)
                        self._keyboard.release(Key.insert)
                elif key_combo == "ctrl_shift_v":
                    with self._keyboard.pressed(Key.ctrl):
                        with self._keyboard.pressed(Key.shift):
                            self._keyboard.press('v')
                            self._keyboard.release('v')
                else:  # ctrl_v
                    with self._keyboard.pressed(Key.ctrl):
                        self._keyboard.press('v')
                        self._keyboard.release('v')
                return True
            except Exception:
                pass

        return False

    # ── Safe Paste Workflow ──────────────────────────────────────────────────

    def paste_with_restore(
        self,
        text: str,
        paste_method: str = "clipboard_restore",
        delay_ms: int = 150,
        key_combo: str = "ctrl_v"
    ) -> bool:
        """High-level paste orchestrator.

        paste_method options:
        - 'clipboard_restore': Stash existing, write text, inject Ctrl+V, quiet wait, restore.
        - 'clipboard_only': Write text to clipboard only (user pastes manually).
        - 'direct_typing': Fall back to simulated character typing.
        """
        if not text:
            return False

        if paste_method == "clipboard_only":
            return self.write_text(text)

        if paste_method == "direct_typing":
            return self.type_directly(text)

        # Standard 'clipboard_restore' workflow:
        # 1. Stash current clipboard & primary selection
        saved_text = self.read_text()
        saved_primary = self.read_primary_text()

        # 2. Write new text to BOTH clipboard and primary
        # (Terminals use PRIMARY for Shift+Insert; GUI apps use CLIPBOARD)
        if not self.write_text(text):
            return False
        self.write_primary_text(text)

        # Brief settle delay before key combo (ensure OS selections updated)
        time.sleep(0.04)

        # 3. Inject paste key chord
        chord_ok = self.inject_paste_chord(key_combo)

        # 4. Quiet consumption window (target app reads clipboard buffer)
        quiet_sec = max(delay_ms, 50) / 1000.0
        time.sleep(quiet_sec)

        # 5. Restore original clipboard & primary selections
        if saved_text is not None and len(saved_text) > 0:
            self.write_text(saved_text)
        else:
            self.clear()

        if saved_primary is not None and len(saved_primary) > 0:
            self.write_primary_text(saved_primary)

        return chord_ok

    def type_directly(self, text: str) -> bool:
        """Simulate character-by-character typing as last resort."""
        if not text:
            return False

        # Wayland ydotool
        if is_tool_available("ydotool"):
            try:
                proc = subprocess.run(["ydotool", "type", "--", text], timeout=10.0, check=False)
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        # X11 xdotool
        if is_tool_available("xdotool"):
            try:
                proc = subprocess.run(["xdotool", "type", "--clearmodifiers", "--", text], timeout=10.0, check=False)
                if proc.returncode == 0:
                    return True
            except Exception:
                pass

        # pynput
        if self._keyboard is not None:
            try:
                self._keyboard.type(text)
                return True
            except Exception:
                pass

        return False


# Global singleton instance
_clipboard_instance: Optional[ClipboardManager] = None


def get_clipboard_manager() -> ClipboardManager:
    """Return the global ClipboardManager singleton."""
    global _clipboard_instance
    if _clipboard_instance is None:
        _clipboard_instance = ClipboardManager()
    return _clipboard_instance
