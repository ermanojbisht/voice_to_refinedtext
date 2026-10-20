"""tests/test_evdev_listener.py.

Unit tests for Linux Evdev physical keyboard listener.
"""

import pytest
from audio_toolkit.evdev_listener import (
    parse_hotkey_to_evdev,
    EvdevHotkeyListener,
    MODIFIER_ECODES,
    _EVDEV_AVAILABLE,
)


def test_parse_hotkey_ctrl_space():
    mods, trigger = parse_hotkey_to_evdev("Ctrl+Space")
    assert "ctrl" in mods
    assert len(mods) == 1
    assert trigger == 57  # KEY_SPACE


def test_parse_hotkey_ctrl_alt_v():
    mods, trigger = parse_hotkey_to_evdev("Ctrl+Alt+V")
    assert "ctrl" in mods
    assert "alt" in mods
    assert len(mods) == 2
    # KEY_V in evdev is 47
    from evdev import ecodes
    assert trigger == ecodes.KEY_V


def test_parse_hotkey_super_shift():
    mods, trigger = parse_hotkey_to_evdev("Super+Shift+A")
    assert "super" in mods
    assert "shift" in mods
    from evdev import ecodes
    assert trigger == ecodes.KEY_A


def test_evdev_is_available():
    # On this Linux box with 'input' group, is_available should return True
    assert EvdevHotkeyListener.is_available() is True


def test_evdev_mock_state_logic():
    listener = EvdevHotkeyListener("Ctrl+Space")
    assert listener._modifiers == {"ctrl"}
    assert listener._trigger_code == 57

    # Test modifier checking logic
    # No keys held:
    assert listener._modifiers_satisfied() is False

    # Ctrl held (code 29):
    listener._held_keys.add(29)
    assert listener._modifiers_satisfied() is True

    # Ctrl + Alt held (code 56):
    listener._held_keys.add(56)
    assert listener._modifiers_satisfied() is False  # Alt was not requested!

    listener._held_keys.discard(56)
    assert listener._modifiers_satisfied() is True

    # Test release checking logic
    assert listener._is_hotkey_release(57) is True  # Space release
    assert listener._is_hotkey_release(29) is True  # Ctrl release
    assert listener._is_hotkey_release(56) is False # Alt release
