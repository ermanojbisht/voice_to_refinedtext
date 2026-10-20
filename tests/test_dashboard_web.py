"""Unit and integration tests for Voice Refiner Web Dashboard & REST API."""
import json
import socket
import time
import urllib.request
import pytest

from refiner_service import RefinerService
import settings_server


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def running_server():
    port = get_free_port()
    settings_server.start_server_daemon(port)
    for _ in range(20):
        if settings_server.is_port_in_use(port):
            break
        time.sleep(0.05)
    return port


def test_refiner_service_singleton():
    svc1 = RefinerService.get_instance()
    svc2 = RefinerService.get_instance()
    assert svc1 is svc2
    status = svc1.get_status()
    assert "visual_state" in status
    assert "language_mode" in status
    assert "active_profile" in status
    assert "recent_clips" in status


def test_refiner_service_modes():
    svc = RefinerService.get_instance()
    original_mode = svc.engine.config.get("LANGUAGE_MODE", "bilingual")
    new_mode = svc.cycle_language_mode()
    assert new_mode != original_mode
    modes = ["bilingual", "pure_english", "pure_hindi", "roman_hinglish"]
    assert new_mode in modes
    svc.engine.config["LANGUAGE_MODE"] = original_mode


def test_dashboard_html_page(running_server):
    url = f"http://127.0.0.1:{running_server}/dashboard"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "AI Voice Refiner" in content
        assert "visualizer-container" in content
        assert "recordBtn" in content
        assert "refinedOutput" in content
        assert "Recent Dictations Today" in content


def test_dashboard_status_api(running_server):
    url = f"http://127.0.0.1:{running_server}/api/refiner/status"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "visual_state" in data
        assert "language_mode" in data
        assert "active_profile" in data
        assert "is_recording" in data
        assert "recent_clips" in data
        assert isinstance(data["recent_clips"], list)


def test_dashboard_cycle_mode_api(running_server):
    url = f"http://127.0.0.1:{running_server}/api/refiner/cycle_mode"
    req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("ok") is True
        assert "language_mode" in data


def test_dashboard_cycle_profile_api(running_server):
    url = f"http://127.0.0.1:{running_server}/api/refiner/cycle_profile"
    req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("ok") is True
        assert "active_profile" in data
