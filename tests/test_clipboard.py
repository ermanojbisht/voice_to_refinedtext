"""tests/test_clipboard.py.

Unit tests for Safe Clipboard Save & Restore Auto-Paste engine.
"""

import subprocess
from unittest.mock import MagicMock, call, patch
import pytest

from audio_toolkit.clipboard import ClipboardManager, get_clipboard_manager, is_wayland


@pytest.fixture
def cb_manager():
    return ClipboardManager()


def test_is_wayland_detection():
    with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
        assert is_wayland() is True
    with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11", "WAYLAND_DISPLAY": ""}, clear=True):
        assert is_wayland() is False


def test_read_text_wayland_wl_paste(cb_manager):
    with patch("audio_toolkit.clipboard.is_wayland", return_value=True), \
         patch("audio_toolkit.clipboard.is_tool_available", side_effect=lambda t: t == "wl-paste"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Stashed user text")
        text = cb_manager.read_text()
        assert text == "Stashed user text"
        mock_run.assert_called_once_with(
            ["wl-paste", "--no-newline"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
            check=False
        )


def test_read_text_x11_xclip(cb_manager):
    with patch("audio_toolkit.clipboard.is_wayland", return_value=False), \
         patch("audio_toolkit.clipboard.is_tool_available", side_effect=lambda t: t == "xclip"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="X11 stashed text")
        text = cb_manager.read_text()
        assert text == "X11 stashed text"
        mock_run.assert_called_once_with(
            ["xclip", "-selection", "clipboard", "-o"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
            check=False
        )


def test_write_text_wayland_wl_copy(cb_manager):
    with patch("audio_toolkit.clipboard.is_wayland", return_value=True), \
         patch("audio_toolkit.clipboard.is_tool_available", side_effect=lambda t: t == "wl-copy"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ok = cb_manager.write_text("नया पाठ (New Text)")
        assert ok is True
        mock_run.assert_called_once_with(
            ["wl-copy", "--", "नया पाठ (New Text)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
            check=False
        )


def test_write_text_x11_xclip(cb_manager):
    with patch("audio_toolkit.clipboard.is_wayland", return_value=False), \
         patch("audio_toolkit.clipboard.is_tool_available", side_effect=lambda t: t == "xclip"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ok = cb_manager.write_text("Hello X11")
        assert ok is True
        mock_run.assert_called_once_with(
            ["xclip", "-selection", "clipboard"],
            input="Hello X11".encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
            check=False
        )


def test_inject_paste_chord_ydotool_raw_keycodes(cb_manager):
    with patch("audio_toolkit.clipboard.is_tool_available", side_effect=lambda t: t == "ydotool"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        # Ctrl+V
        ok = cb_manager.inject_paste_chord("ctrl_v")
        assert ok is True
        mock_run.assert_called_with(
            ["ydotool", "key", "-d", "20", "29:1", "47:1", "47:0", "29:0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
            check=False
        )

        # Shift+Insert (terminals)
        ok = cb_manager.inject_paste_chord("shift_insert")
        assert ok is True
        mock_run.assert_called_with(
            ["ydotool", "key", "-d", "20", "42:1", "110:1", "110:0", "42:0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
            check=False
        )


def test_inject_paste_chord_xdotool_fallback(cb_manager):
    with patch("audio_toolkit.clipboard.is_tool_available", side_effect=lambda t: t == "xdotool"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ok = cb_manager.inject_paste_chord("ctrl_v")
        assert ok is True
        mock_run.assert_called_once_with(
            ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
            check=False
        )


def test_paste_with_restore_full_cycle(cb_manager):
    with patch.object(cb_manager, "read_text", return_value="https://example.com/secret") as mock_read, \
         patch.object(cb_manager, "write_text", return_value=True) as mock_write, \
         patch.object(cb_manager, "inject_paste_chord", return_value=True) as mock_chord, \
         patch("time.sleep") as mock_sleep:

        ok = cb_manager.paste_with_restore(
            text="Refined dictation text",
            paste_method="clipboard_restore",
            delay_ms=100,
            key_combo="ctrl_v"
        )
        assert ok is True
        mock_read.assert_called_once()
        mock_chord.assert_called_once_with("ctrl_v")

        # Verify write sequence: first refined text, then restore original
        expected_writes = [call("Refined dictation text"), call("https://example.com/secret")]
        assert mock_write.call_args_list == expected_writes

        # Verify quiet period delay called (0.1s for 100ms)
        mock_sleep.assert_any_call(0.1)


def test_paste_with_restore_empty_initial(cb_manager):
    with patch.object(cb_manager, "read_text", return_value="") as mock_read, \
         patch.object(cb_manager, "write_text", return_value=True) as mock_write, \
         patch.object(cb_manager, "clear", return_value=True) as mock_clear, \
         patch.object(cb_manager, "inject_paste_chord", return_value=True), \
         patch("time.sleep"):

        ok = cb_manager.paste_with_restore("Refined text", paste_method="clipboard_restore")
        assert ok is True
        mock_write.assert_called_once_with("Refined text")
        mock_clear.assert_called_once()


def test_paste_modes(cb_manager):
    # clipboard_only mode
    with patch.object(cb_manager, "write_text", return_value=True) as mock_write, \
         patch.object(cb_manager, "inject_paste_chord") as mock_chord:
        ok = cb_manager.paste_with_restore("Only copy", paste_method="clipboard_only")
        assert ok is True
        mock_write.assert_called_once_with("Only copy")
        mock_chord.assert_not_called()

    # direct_typing mode
    with patch.object(cb_manager, "type_directly", return_value=True) as mock_type:
        ok = cb_manager.paste_with_restore("Type me", paste_method="direct_typing")
        assert ok is True
        mock_type.assert_called_once_with("Type me")


def test_get_clipboard_manager_singleton():
    m1 = get_clipboard_manager()
    m2 = get_clipboard_manager()
    assert m1 is m2
    assert isinstance(m1, ClipboardManager)
