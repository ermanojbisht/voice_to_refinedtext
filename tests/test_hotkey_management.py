"""Unit and integration tests for unified global hotkey management."""
import os
import json
import pytest
from pynput import keyboard

import utils
from refiner_service import RefinerService
from review_service import ReviewService


def test_hotkey_display_formatting():
    assert utils.format_hotkey_display("ctrl+space") == "Ctrl+Space"
    assert utils.format_hotkey_display("<Control>space") == "Ctrl+Space"
    assert utils.format_hotkey_display("Ctrl+Alt+V") == "Ctrl+Alt+V"
    assert utils.format_hotkey_display("<Control><Alt>v") == "Ctrl+Alt+V"
    assert utils.format_hotkey_display("<ctrl>+<shift>+<space>") == "Ctrl+Shift+Space"
    assert utils.format_hotkey_display("") == "Ctrl+Space"


def test_hotkey_gnome_formatting():
    assert utils.format_hotkey_gnome("Ctrl+Space") == "<Control>space"
    assert utils.format_hotkey_gnome("ctrl+alt+v") == "<Control><Alt>v"
    assert utils.format_hotkey_gnome("<Control>space") == "<Control>space"
    assert utils.format_hotkey_gnome("Ctrl+Shift+Return") == "<Control><Shift>Return"


def test_hotkey_parsing():
    mods, trigger = utils.parse_hotkey("Ctrl+Space")
    assert mods == {"ctrl"}
    assert trigger == keyboard.Key.space

    mods, trigger = utils.parse_hotkey("Ctrl+Alt+V")
    assert mods == {"ctrl", "alt"}
    assert trigger == "v"

    mods, trigger = utils.parse_hotkey("<Control>space")
    assert mods == {"ctrl"}
    assert trigger == keyboard.Key.space


def test_hotkey_matching():
    mods, trigger = utils.parse_hotkey("Ctrl+Space")

    # Match: Ctrl held down, Space pressed
    pressed_keys = {keyboard.Key.ctrl_l}
    assert utils.matches_hotkey(pressed_keys, keyboard.Key.space, mods, trigger) is True

    # Mismatch: Alt also held down (Ctrl+Alt+Space != Ctrl+Space)
    pressed_keys = {keyboard.Key.ctrl_l, keyboard.Key.alt_l}
    assert utils.matches_hotkey(pressed_keys, keyboard.Key.space, mods, trigger) is False

    # Mismatch: Ctrl not held down
    pressed_keys = set()
    assert utils.matches_hotkey(pressed_keys, keyboard.Key.space, mods, trigger) is False

    # Mismatch: Wrong trigger key pressed
    pressed_keys = {keyboard.Key.ctrl_l}
    assert utils.matches_hotkey(pressed_keys, keyboard.Key.enter, mods, trigger) is False


def test_hotkey_matching_char_keys():
    mods, trigger = utils.parse_hotkey("Ctrl+Alt+V")

    # Match
    pressed_keys = {keyboard.Key.ctrl, keyboard.Key.alt}
    v_key = keyboard.KeyCode(char="v")
    assert utils.matches_hotkey(pressed_keys, v_key, mods, trigger) is True

    # Mismatch char
    s_key = keyboard.KeyCode(char="s")
    assert utils.matches_hotkey(pressed_keys, s_key, mods, trigger) is False


def test_get_global_hotkey():
    assert utils.get_global_hotkey({"GLOBAL_HOTKEY": "Ctrl+Alt+V"}) == "Ctrl+Alt+V"
    assert utils.get_global_hotkey({"GLOBAL_HOTKEY": "<Control>space"}) == "Ctrl+Space"
    assert utils.get_global_hotkey({}) == "Ctrl+Space"


def test_refiner_and_review_services_expose_hotkey():
    ref_svc = RefinerService.get_instance()
    status = ref_svc.get_status()
    assert "global_hotkey" in status
    assert status["global_hotkey"] in ("Ctrl+Space", "Ctrl+Alt+V")

    rev_svc = ReviewService.get_instance()
    state = rev_svc.get_state()
    assert "global_hotkey" in state
    assert state["global_hotkey"] in ("Ctrl+Space", "Ctrl+Alt+V")


def test_is_hotkey_release():
    from pynput import keyboard
    mods, trigger = utils.parse_hotkey("Ctrl+Space")

    # Space release -> True
    assert utils.is_hotkey_release(keyboard.Key.space, mods, trigger) is True
    # Ctrl release -> True
    assert utils.is_hotkey_release(keyboard.Key.ctrl_l, mods, trigger) is True
    # Alt release -> False (not in Ctrl+Space)
    assert utils.is_hotkey_release(keyboard.Key.alt, mods, trigger) is False
    # Letter key release -> False
    assert utils.is_hotkey_release(keyboard.KeyCode(char="a"), mods, trigger) is False
