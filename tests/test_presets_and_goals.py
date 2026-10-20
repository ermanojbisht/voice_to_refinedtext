"""Unit and integration tests for Decoupled ASR Presets and LLM Refinement Goals."""
import json
import os
import wave
import numpy as np
import pytest
from unittest.mock import Mock, patch

from engine import VoiceEngine
from refiner_service import RefinerService
import settings_server


@pytest.fixture
def temp_engine(tmp_path):
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with patch("pynput.keyboard.Controller", Mock()):
        eng = VoiceEngine(repo_root)
        eng.log = Mock()
        return eng


def test_config_contains_presets_and_goals(temp_engine):
    """Verify config contains ASR_PRESETS and REFINEMENT_GOALS with expected structure."""
    cfg = temp_engine.config
    assert "ASR_PRESETS" in cfg
    assert "REFINEMENT_GOALS" in cfg
    assert "ACTIVE_ASR_PRESET" in cfg
    assert "ACTIVE_REFINEMENT_GOAL" in cfg
    assert "WHISPER_FALLBACK_MODEL" in cfg

    presets = cfg["ASR_PRESETS"]
    assert "smart_bilingual" in presets
    assert "instant_english" in presets
    assert "instant_hindi" in presets
    assert "roman_hinglish" in presets

    for key, p in presets.items():
        assert "label" in p
        assert "backend" in p
        assert "description" in p
        assert len(p["description"]) > 5

    goals = cfg["REFINEMENT_GOALS"]
    assert "clean_bilingual" in goals
    assert "official_english" in goals
    assert "official_hindi" in goals
    assert "concise_summary" in goals
    assert "ideas_actions" in goals
    assert "roman_hinglish" in goals

    for key, g in goals.items():
        assert "label" in g
        assert "description" in g
        assert "output_lang" in g
        assert len(g["description"]) > 5


def test_engine_preset_and_goal_accessors(temp_engine):
    """Verify get/set for presets and goals in VoiceEngine."""
    cur_p = temp_engine.get_active_preset()
    assert cur_p in temp_engine.config["ASR_PRESETS"]

    temp_engine.set_active_preset("instant_english")
    assert temp_engine.get_active_preset() == "instant_english"
    assert temp_engine.config["ACTIVE_ASR_PRESET"] == "instant_english"

    cur_g = temp_engine.get_active_goal()
    assert cur_g in temp_engine.config["REFINEMENT_GOALS"]

    temp_engine.set_active_goal("official_english")
    assert temp_engine.get_active_goal() == "official_english"
    assert temp_engine.config["ACTIVE_REFINEMENT_GOAL"] == "official_english"


def test_refiner_service_cycles_presets_and_goals():
    """Verify RefinerService cycles presets and goals cleanly."""
    svc = RefinerService.get_instance()
    initial_preset = svc.engine.get_active_preset()
    new_preset = svc.cycle_preset()
    assert new_preset != initial_preset
    status = svc.get_status()
    assert status["active_preset"] == new_preset
    assert "active_preset_label" in status
    assert "active_preset_desc" in status

    initial_goal = svc.engine.get_active_goal()
    new_goal = svc.cycle_goal()
    assert new_goal != initial_goal
    status = svc.get_status()
    assert status["active_goal"] == new_goal
    assert "active_goal_label" in status
    assert "active_goal_desc" in status


def test_reprocess_last_audio(temp_engine, tmp_path, monkeypatch):
    """Verify re-processing re-runs transcription and refinement on input.wav."""
    wav_path = os.path.join(temp_engine.script_dir, "input.wav")
    original_bytes = None
    if os.path.isfile(wav_path):
        with open(wav_path, "rb") as f:
            original_bytes = f.read()

    try:
        # Write dummy wav for test
        samples = (np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000)) * 16384).astype(np.int16)
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(samples.tobytes())

        monkeypatch.setattr(temp_engine, "transcribe", lambda path: "The e.e. inspected the road.")
        monkeypatch.setattr(temp_engine, "refine", lambda text, mode=None, goal=None: "The EE inspected the road.")

        res = temp_engine.reprocess_last_audio(preset="smart_bilingual", goal="clean_bilingual")
        assert res.get("ok") is True
        assert res.get("raw_text") == "The e.e. inspected the road."
        assert res.get("final_text") == "The EE inspected the road."
    finally:
        if original_bytes is not None:
            with open(wav_path, "wb") as f:
                f.write(original_bytes)


def test_web_settings_no_standalone_backend_dropdown():
    """Verify that the standalone Engine Backend dropdown has been eliminated."""
    html_path = os.path.join(settings_server.SCRIPT_DIR, "web_settings", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Standalone select id="main_ASR_ENGINE" should be removed
    assert 'id="main_ASR_ENGINE"' not in content
    # Presets grid and Refinement Goal select should be present
    assert 'id="presetGrid"' in content
    assert 'id="main_REFINEMENT_GOAL"' in content
    assert 'id="goalDescription"' in content


def test_tray_app_live_config_sync(tmp_path, monkeypatch):
    """Verify tray app detects disk config changes and updates without restart."""
    import tray_app
    with patch("pynput.keyboard.Controller", Mock()), \
         patch("pynput.keyboard.Listener", Mock()), \
         patch.object(tray_app.VoiceAssistantTray, "_background_prewarm", Mock()), \
         patch("settings_server.start_server_daemon", Mock()):
        tray = tray_app.VoiceAssistantTray()
        initial_preset = tray.engine.get_active_preset()

        # Simulate web settings save by modifying config.json
        cfg_path = os.path.join(tray.script_dir, "config.json")
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        orig_preset = data.get("ACTIVE_ASR_PRESET")
        new_preset = "instant_hindi" if orig_preset != "instant_hindi" else "instant_english"
        data["ACTIVE_ASR_PRESET"] = new_preset
        data["ACTIVE_MODEL_PROFILE"] = new_preset

        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Trigger sync
            tray._sync_config_from_disk()

            assert tray.engine.get_active_preset() == new_preset
            lbl = tray.engine.config["ASR_PRESETS"][new_preset]["label"]
            assert lbl in tray.icon.title
        finally:
            data["ACTIVE_ASR_PRESET"] = orig_preset
            data["ACTIVE_MODEL_PROFILE"] = orig_preset
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            tray._sync_config_from_disk()
            tray.running = False


def test_acoustic_suggestion_on_transcription(temp_engine):
    """Verify acoustic check suggests appropriate preset without modifying user selection."""
    wav_path = os.path.join(temp_engine.script_dir, "benchmarks", "recordings", "script3.wav")
    if not os.path.isfile(wav_path):
        pytest.skip("script3.wav not found")

    temp_engine.set_active_preset("instant_english")
    mock_asr = Mock()
    mock_asr.transcribe.return_value = Mock(text="transcribed sample text")
    temp_engine._asr_provider = mock_asr

    with patch.object(temp_engine, "notify_acoustic_suggestion") as mock_notify:
        raw = temp_engine.transcribe(wav_path)
        assert raw == "transcribed sample text"
        # User preset is preserved 100%
        assert temp_engine.get_active_preset() == "instant_english"
        # Mismatch notification was fired
        assert mock_notify.called
        sug = mock_notify.call_args[0][0]
        assert sug["is_mismatch"] is True
        assert sug["suggested_preset"] in ("instant_hindi", "smart_bilingual")


def test_reprocess_tray_and_dashboard_consistency(temp_engine, monkeypatch):
    """Verify tray and dashboard use consistent result flow, read final_text, and copy to clipboard."""
    wav_path = os.path.join(temp_engine.script_dir, "input.wav")
    original_bytes = None
    if os.path.isfile(wav_path):
        with open(wav_path, "rb") as f:
            original_bytes = f.read()

    try:
        # Create test wav
        samples = (np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, 8000)) * 16384).astype(np.int16)
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(samples.tobytes())

        monkeypatch.setattr(temp_engine, "transcribe", lambda path: "raw speech text")
        monkeypatch.setattr(temp_engine, "refine", lambda text, mode=None, goal=None: "Refined Text Output.")

        ref_svc = RefinerService.get_instance()
        ref_svc.engine = temp_engine

        # Test RefinerService synchronous reprocessing
        with patch("subprocess.run") as mock_xclip:
            res = ref_svc.reprocess_last_sync(preset="instant_english", goal="official_english")
            assert res.get("ok") is True
            assert res.get("final_text") == "Refined Text Output."
            assert res.get("text") == "Refined Text Output."
            assert ref_svc.last_refined_text == "Refined Text Output."
            # Verified clip appended to history
            assert any(c.get("text") == "Refined Text Output." and c.get("reprocessed") is True for c in ref_svc.recent_clips)
            # Verified xclip was called
            assert mock_xclip.called
            xclip_cmd = mock_xclip.call_args[0][0]
            assert "xclip" in xclip_cmd

        # Test input.wav remains intact for consecutive runs
        assert os.path.isfile(wav_path)

        # Test tray reprocessing flow
        import tray_app
        with patch("pynput.keyboard.Controller", Mock()), \
             patch("pynput.keyboard.Listener", Mock()), \
             patch.object(tray_app.VoiceAssistantTray, "_background_prewarm", Mock()), \
             patch("settings_server.start_server_daemon", Mock()):
            tray = tray_app.VoiceAssistantTray()
            tray.engine = temp_engine

            with patch.object(tray, "_notify") as mock_tray_notify:
                # Trigger worker synchronously for testing
                tray.reprocess_last_audio()
                # Wait briefly for daemon thread worker
                import time
                time.sleep(0.1)

                assert mock_tray_notify.called
                notifications = [call[0][1] for call in mock_tray_notify.call_args_list]
                assert any("Refined Text Output" in n for n in notifications)
            tray.running = False

    finally:
        if original_bytes is not None:
            with open(wav_path, "wb") as f:
                f.write(original_bytes)
        elif os.path.isfile(wav_path):
            os.remove(wav_path)



