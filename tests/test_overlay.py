"""tests/test_overlay.py.

Unit tests for Floating Pill Recording Overlay & Live Waveform Canvas (Track B).
"""

from unittest.mock import MagicMock, patch
import pytest

from audio_toolkit.overlay import RecordingOverlay, get_recording_overlay


@pytest.fixture
def overlay_mock():
    with patch("audio_toolkit.overlay.RecordingOverlay._start_thread"):
        ov = RecordingOverlay()
        ov._root = MagicMock()
        ov._canvas = MagicMock()
        ov._icon_label = MagicMock()
        ov._text_label = MagicMock()
        return ov


def test_overlay_state_queue_events(overlay_mock):
    # show_listening
    overlay_mock.show_listening()
    cmd, args = overlay_mock._cmd_queue.get_nowait()
    assert cmd == "show_listening"
    assert args is None

    # update_level
    overlay_mock.update_level(450.5)
    cmd, args = overlay_mock._cmd_queue.get_nowait()
    assert cmd == "update_level"
    assert args == 450.5

    # show_thinking
    overlay_mock.show_thinking()
    cmd, args = overlay_mock._cmd_queue.get_nowait()
    assert cmd == "show_thinking"

    # show_done
    overlay_mock.show_done("Pasted!")
    cmd, args = overlay_mock._cmd_queue.get_nowait()
    assert cmd == "show_done"
    assert args == "Pasted!"

    # hide
    overlay_mock.hide()
    cmd, args = overlay_mock._cmd_queue.get_nowait()
    assert cmd == "hide"

    # set_position
    overlay_mock.set_position("bottom")
    cmd, args = overlay_mock._cmd_queue.get_nowait()
    assert cmd == "set_position"
    assert args == "bottom"

    # set_style
    overlay_mock.set_style("stagnant")
    cmd, args = overlay_mock._cmd_queue.get_nowait()
    assert cmd == "set_style"
    assert args == "stagnant"


def test_overlay_state_handlers(overlay_mock):
    # Listening handler
    overlay_mock._do_show_listening()
    assert overlay_mock._state == "listening"
    overlay_mock._icon_label.config.assert_called_with(text="🎙", fg="#f38ba8")
    overlay_mock._text_label.config.assert_called_with(text="Listening...", fg="#f38ba8")
    overlay_mock._root.deiconify.assert_called_once()

    # Level update handler
    overlay_mock._do_update_level(500.0)
    assert overlay_mock._rms_level == 500.0

    # Thinking handler
    overlay_mock._do_show_thinking()
    assert overlay_mock._state == "thinking"
    overlay_mock._icon_label.config.assert_called_with(text="🧠", fg="#b4befe")

    # Done handler
    overlay_mock._do_show_done("Pasted!")
    assert overlay_mock._state == "done"
    overlay_mock._text_label.config.assert_called_with(text="Pasted!", fg="#a6e3a1")

    # Hide handler
    overlay_mock._do_hide()
    assert overlay_mock._state == "hidden"
    overlay_mock._root.withdraw.assert_called_once()


def test_get_recording_overlay_singleton():
    with patch("audio_toolkit.overlay.RecordingOverlay._start_thread"):
        o1 = get_recording_overlay()
        o2 = get_recording_overlay()
        assert o1 is o2
        assert isinstance(o1, RecordingOverlay)
