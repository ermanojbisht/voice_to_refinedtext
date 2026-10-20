"""audio_toolkit/evdev_listener.py.

Linux Kernel Evdev Physical Keyboard Listener.
Bypasses Wayland window restrictions to capture genuine physical key press (1)
and physical key release (0) events with zero interference from OS auto-repeat (2).

Works seamlessly on Ubuntu 22.04 through 26.04 when user has access to /dev/input/event*
(standard for users in the 'input' group).
"""

from __future__ import annotations

import logging
import os
import re
import select
import threading
import time
from typing import Callable, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

try:
    import evdev
    from evdev import ecodes
    _EVDEV_AVAILABLE = True
except ImportError:
    _EVDEV_AVAILABLE = False
    ecodes = None


MODIFIER_ECODES = {
    "ctrl": {29, 97},    # KEY_LEFTCTRL, KEY_RIGHTCTRL
    "alt": {56, 100},    # KEY_LEFTALT, KEY_RIGHTALT
    "shift": {42, 54},   # KEY_LEFTSHIFT, KEY_RIGHTSHIFT
    "super": {125, 126}, # KEY_LEFTMETA, KEY_RIGHTMETA
}

SPECIAL_KEY_MAP = {
    "space": 57,      # KEY_SPACE
    "enter": 28,      # KEY_ENTER
    "return": 28,     # KEY_ENTER
    "tab": 15,        # KEY_TAB
    "esc": 1,         # KEY_ESC
    "escape": 1,      # KEY_ESC
    "backspace": 14,  # KEY_BACKSPACE
    "capslock": 58,   # KEY_CAPSLOCK
    "f1": 59, "f2": 60, "f3": 61, "f4": 62, "f5": 63, "f6": 64,
    "f7": 65, "f8": 66, "f9": 67, "f10": 68, "f11": 87, "f12": 88,
}


def parse_hotkey_to_evdev(hotkey_str: str) -> Tuple[Set[str], Optional[int]]:
    """Parses a hotkey string (e.g. 'Ctrl+Space', 'Ctrl+Alt+V') into required modifier groups and a trigger ecode."""
    if not _EVDEV_AVAILABLE or not ecodes:
        return set(), None

    tokens = [t.strip().lower() for t in re.split(r"[+_-]", hotkey_str) if t.strip()]
    modifiers: Set[str] = set()
    trigger_code: Optional[int] = None

    for tok in tokens:
        if tok in ("ctrl", "control"):
            modifiers.add("ctrl")
        elif tok in ("alt", "opt", "option"):
            modifiers.add("alt")
        elif tok in ("shift",):
            modifiers.add("shift")
        elif tok in ("super", "win", "cmd", "meta"):
            modifiers.add("super")
        elif tok in SPECIAL_KEY_MAP:
            trigger_code = SPECIAL_KEY_MAP[tok]
        elif len(tok) == 1 and tok.isalnum():
            # Letter or number key
            attr_name = f"KEY_{tok.upper()}"
            trigger_code = getattr(ecodes, attr_name, None)
        else:
            # Fallback check
            attr_name = f"KEY_{tok.upper()}"
            if hasattr(ecodes, attr_name):
                trigger_code = getattr(ecodes, attr_name)

    if trigger_code is None:
        trigger_code = ecodes.KEY_SPACE

    return modifiers, trigger_code


class EvdevHotkeyListener:
    """Listens for hardware keyboard events via Linux /dev/input/event* interfaces."""

    def __init__(
        self,
        hotkey_str: str = "Ctrl+Space",
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
    ):
        self._hotkey_str = hotkey_str
        self._on_press = on_press
        self._on_release = on_release
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._devices: List[evdev.InputDevice] = []
        self._held_keys: Set[int] = set()
        self._lock = threading.Lock()

        self._modifiers, self._trigger_code = parse_hotkey_to_evdev(hotkey_str)

    @classmethod
    def is_available(cls) -> bool:
        """Returns True if evdev is installed and user has read access to /dev/input."""
        if not _EVDEV_AVAILABLE:
            return False
        try:
            dev_paths = evdev.list_devices()
            if not dev_paths:
                return False
            # Check read permission on at least one device
            for p in dev_paths:
                if os.access(p, os.R_OK):
                    return True
            return False
        except Exception:
            return False

    def update_hotkey(self, hotkey_str: str) -> None:
        with self._lock:
            self._hotkey_str = hotkey_str
            self._modifiers, self._trigger_code = parse_hotkey_to_evdev(hotkey_str)
            logger.info("EvdevHotkeyListener updated hotkey: %s (trigger=%s)", hotkey_str, self._trigger_code)

    def _find_keyboards(self) -> List[evdev.InputDevice]:
        keyboards = []
        try:
            for path in evdev.list_devices():
                try:
                    dev = evdev.InputDevice(path)
                    name_lower = dev.name.lower()
                    # Skip virtual uinput injection devices (e.g. ydotool)
                    if "ydotool" in name_lower or "uinput" in name_lower:
                        continue
                    caps = dev.capabilities()
                    if ecodes.EV_KEY in caps:
                        keys = caps[ecodes.EV_KEY]
                        # Must have Space and Enter to qualify as a physical keyboard
                        if ecodes.KEY_SPACE in keys and ecodes.KEY_ENTER in keys:
                            keyboards.append(dev)
                except (PermissionError, OSError):
                    continue
        except Exception as e:
            logger.warning("Error enumerating evdev devices: %s", e)
        return keyboards

    def start(self) -> bool:
        """Starts listening in a background daemon thread."""
        if not self.is_available():
            logger.warning("evdev listener not available (missing permissions or package)")
            return False

        self._devices = self._find_keyboards()
        if not self._devices:
            logger.warning("No physical keyboard devices found accessible via evdev")
            return False

        logger.info(
            "EvdevHotkeyListener found %d keyboard(s): %s",
            len(self._devices),
            [d.name for d in self._devices]
        )

        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="EvdevListenerThread")
        self._thread.start()
        return True

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._devices.clear()

    def _modifiers_satisfied(self) -> bool:
        """Checks if all required modifier groups are held down, and no unrequested modifiers are held."""
        for mod_name, ec_set in MODIFIER_ECODES.items():
            is_held = any(k in self._held_keys for k in ec_set)
            required = mod_name in self._modifiers
            if is_held != required:
                return False
        return True

    def _is_hotkey_release(self, code: int) -> bool:
        """Checks if the released key is the trigger key or one of the required modifiers."""
        if code == self._trigger_code:
            return True
        for mod_name in self._modifiers:
            if code in MODIFIER_ECODES.get(mod_name, set()):
                return True
        return False

    def _poll_loop(self) -> None:
        while self._running and self._devices:
            try:
                r, _, _ = select.select(self._devices, [], [], 0.5)
                for dev in r:
                    try:
                        for event in dev.read():
                            if event.type != ecodes.EV_KEY:
                                continue

                            code = event.code
                            val = event.value

                            # ── Auto-repeat (val == 2): SILENTLY IGNORE! ──
                            if val == 2:
                                continue

                            with self._lock:
                                if val == 1:  # Physical Key Down
                                    self._held_keys.add(code)
                                    if code == self._trigger_code and self._modifiers_satisfied():
                                        logger.debug("Evdev: Hotkey down detected (code=%d)", code)
                                        if self._on_press:
                                            try:
                                                self._on_press()
                                            except Exception as exc:
                                                logger.error("Error in on_press callback: %s", exc)

                                elif val == 0:  # Physical Key Up
                                    if self._is_hotkey_release(code):
                                        logger.debug("Evdev: Hotkey release detected (code=%d)", code)
                                        if self._on_release:
                                            try:
                                                self._on_release()
                                            except Exception as exc:
                                                logger.error("Error in on_release callback: %s", exc)
                                    self._held_keys.discard(code)

                    except (OSError, PermissionError):
                        # Device disconnected or error
                        pass
            except Exception as e:
                if self._running:
                    logger.debug("Evdev poll loop error: %s", e)
                time.sleep(0.5)
