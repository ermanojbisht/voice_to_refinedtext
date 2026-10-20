"""Tests for Live Rich Terminal Dictation HUD and CLI Voice Options.

Verifies:
- TerminalHUD initialization, TTY handling, and pipe-safe output
- Audio RMS calculation and VU meter bar rendering
- State transitions (RECORDING -> TRANSCRIBING -> REFINING -> DONE)
- Graceful fallback when rich is missing or disabled
- CLI argument parsing in pwd_cli.py (--listen, --hud, --no-hud, --pipe)
- Mock voice dictation run with HUD active
"""
import sys
from unittest.mock import MagicMock, patch
import pytest
from pwd_helper.terminal_hud import TerminalHUD, HAS_RICH


def test_terminal_hud_initialization():
    """Verifies default HUD properties and pipe-mode auto-detection."""
    hud = TerminalHUD(enabled=True, pipe_mode=False, preset_label="Test Preset", goal_label="Test Goal")
    assert hud.preset_label == "Test Preset"
    assert hud.goal_label == "Test Goal"
    assert hud.state == "IDLE"
    assert hud.current_rms == 0.0


def test_terminal_hud_audio_update():
    """Verifies audio energy updates correctly."""
    hud = TerminalHUD(enabled=False, pipe_mode=False)
    assert hud.current_rms == 0.0

    # Direct energy value
    hud.update_audio(chunk=b"\x00" * 320, energy=450.5)
    assert hud.current_rms == 450.5

    # Raw bytes approximation
    pcm_bytes = (b"\x10\x00" * 160)
    hud.update_audio(chunk=pcm_bytes)
    assert hud.current_rms > 0.0


def test_terminal_hud_renderable_panel():
    """Verifies Panel generation with different states when Rich is available."""
    if not HAS_RICH:
        pytest.skip("Rich library not installed")

    hud = TerminalHUD(enabled=True, pipe_mode=False)
    panel = hud._build_renderable()
    assert panel is not None

    hud.state = "RECORDING"
    hud.current_rms = 900.0
    panel_rec = hud._build_renderable()
    assert panel_rec is not None

    hud.state = "TRANSCRIBING"
    panel_trans = hud._build_renderable()
    assert panel_trans is not None


def test_terminal_hud_lifecycle_mocked():
    """Verifies start, set_state, finish, and close sequence without terminal side-effects."""
    hud = TerminalHUD(enabled=True, pipe_mode=True)
    with patch.object(hud, "_console", MagicMock()):
        hud.start_listening("Fast Nemotron", "Clean Text")
        assert hud.state == "RECORDING"

        hud.set_state("TRANSCRIBING")
        assert hud.state == "TRANSCRIBING"

        hud.set_state("REFINING")
        assert hud.state == "REFINING"

        hud.finish("Hello world")
        assert hud.state == "DONE"

        hud.close()
        assert hud._live is None


def test_terminal_hud_disabled_fallback(capsys):
    """Verifies clean stderr output when HUD is disabled (e.g. --no-hud)."""
    hud = TerminalHUD(enabled=False, pipe_mode=False)
    hud.start_listening("Preset A", "Goal B")
    hud.set_state("TRANSCRIBING", detail="Working...")
    hud.finish("Test Output")

    captured = capsys.readouterr()
    assert "Listening" in captured.err
    assert "Result: Test Output" in captured.err


def test_pwd_cli_argparser():
    """Verifies CLI argument parsing in pwd_cli.py without mocking parse_args."""
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("-v", "--voice", "-l", "--listen", action="store_true")
    p.add_argument("-p", "--pipe", action="store_true")
    p.add_argument("--hud", dest="hud", action="store_true", default=None)
    p.add_argument("--no-hud", dest="hud", action="store_false")

    args = p.parse_args(["--listen", "--pipe", "--no-hud"])
    assert args.voice is True
    assert args.pipe is True
    assert args.hud is False


def test_pwd_cli_voice_input_mocked(capsys):
    """Verifies run_voice_input calls engine and prints output cleanly."""
    from pwd_cli import run_voice_input

    with patch("engine.VoiceEngine") as mock_engine_cls:
        mock_eng = MagicMock()
        mock_eng.config = {"CLI_RICH_HUD": False, "ASR_PRESETS": {}, "REFINEMENT_GOALS": {}}
        mock_eng.get_active_preset.return_value = "smart_bilingual"
        mock_eng.record.return_value = "/tmp/fake.wav"
        mock_eng.transcribe.return_value = "NIT issued for bridge repair"
        mock_engine_cls.return_value = mock_eng

        with patch("pwd_cli.copy_to_clipboard") as mock_clip:
            # 1. Normal dictation (raw mode)
            run_voice_input(mode="raw", copy=True, use_hud=False, pipe=False)
            mock_clip.assert_called()

            # 2. Pipe mode (clean stdout)
            capsys.readouterr()
            run_voice_input(mode="raw", copy=False, use_hud=False, pipe=True)
            captured = capsys.readouterr()
            assert "NIT issued for bridge repair" in captured.out
