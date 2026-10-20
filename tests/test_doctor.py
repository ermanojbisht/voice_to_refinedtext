"""Unit and integration tests for doctor.py."""
import json
import subprocess
import sys
import pytest

import doctor


def test_check_python_environment():
    results = doctor.check_python_environment()
    assert len(results) >= 4
    categories = {r.category for r in results}
    assert "Python Environment" in categories
    for r in results:
        assert r.status in ("PASS", "WARN", "FAIL")


def test_check_models_and_portability(tmp_path):
    fake_config = {
        "MODELS_DIR": str(tmp_path),
        "ASR_PRESETS": {
            "test_preset": {
                "label": "Test Preset",
                "backend": "faster_whisper",
                "model": "large-v3-turbo",
            }
        }
    }
    results = doctor.check_models_and_portability(fake_config)
    assert len(results) >= 2
    names = [r.name for r in results]
    assert "MODELS_DIR Path" in names


def test_check_audio_hardware():
    results = doctor.check_audio_hardware(run_mic_probe=False)
    assert len(results) >= 1
    for r in results:
        assert r.category == "Audio Hardware"


def test_check_desktop_and_hotkeys():
    results = doctor.check_desktop_and_hotkeys()
    assert len(results) >= 2
    names = [r.name for r in results]
    assert "Display Server" in names


def test_check_batch_and_cli_tools():
    results = doctor.check_batch_and_cli_tools()
    assert len(results) >= 1
    assert any("FFmpeg" in r.name for r in results)


def test_run_all_checks_and_to_dict():
    report = doctor.run_all_checks(run_mic=False)
    assert report.overall_status in ("PASS", "WARN", "FAIL")
    assert report.platform == sys.platform
    assert len(report.checks) > 5

    data = report.to_dict()
    assert "overall_status" in data
    assert "checks" in data
    assert "remediations" in data
    assert isinstance(data["checks"], list)
    assert isinstance(data["remediations"], list)


def test_doctor_cli_json():
    proc = subprocess.run(
        [sys.executable, "doctor.py", "--json"],
        capture_output=True,
        text=True,
        cwd=doctor.PROJECT_ROOT,
    )
    assert proc.returncode in (0, 1)
    
    # Strip any potential vulkan / stderr loader logs and parse json
    stdout = proc.stdout.strip()
    json_start = stdout.find("{")
    assert json_start != -1, f"No JSON found in stdout: {stdout}"
    data = json.loads(stdout[json_start:])
    assert "overall_status" in data
    assert len(data["checks"]) > 0
