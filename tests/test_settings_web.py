"""Tests for settings_server, config_web_launcher, and manual live-sync."""
import os
import time
import json
import socket
import urllib.request
import pytest

import settings_server
from manual_service import ManualService


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def running_server():
    port = get_free_port()
    settings_server.start_server_daemon(port)
    # wait for server
    for _ in range(20):
        if settings_server.is_port_in_use(port):
            break
        time.sleep(0.05)
    return port


def test_api_health(running_server):
    url = f"http://127.0.0.1:{running_server}/api/health"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("status") == "ok"
        assert "pid" in data


def test_api_config(running_server):
    url = f"http://127.0.0.1:{running_server}/api/config"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "main" in data
        assert "review" in data
        assert "profiles" in data
        assert "active_profile" in data
        assert "features_def" in data
        assert len(data["features_def"]) >= 5
        assert data["main"].get("PASTE_METHOD") in ["clipboard_restore", "clipboard_only", "direct_typing"]
        assert "PASTE_DELAY_MS" in data["main"]
        assert "PASTE_KEY_COMBO" in data["main"]


def test_api_models(running_server):
    url = f"http://127.0.0.1:{running_server}/api/models"
    with urllib.request.urlopen(url, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "models" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) >= 1


def test_manual_auto_rebuild_on_doc_change(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    doc_file = docs_dir / "CONFIGURATION_GUIDE.md"
    doc_file.write_text("# Chapter 1\n\n## 1. Initial Guide\nContent A\n", encoding="utf-8")

    service = ManualService(script_dir=str(tmp_path))
    html1 = service.generate_html_manual()
    assert os.path.isfile(html1)
    t1 = os.path.getmtime(html1)
    content1 = open(html1, "r", encoding="utf-8").read()
    assert "Initial Guide" in content1

    # Modify markdown document
    time.sleep(0.05)
    doc_file.write_text("# Chapter 1\n\n## 1. Updated Guide Edition 2\nBrand New Content\n", encoding="utf-8")
    # Touch file to guarantee distinct mtime
    os.utime(doc_file, (time.time() + 1, time.time() + 1))

    # Without force=True, generate_html_manual should detect the newer markdown and recompile!
    html2 = service.generate_html_manual()
    assert html2 == html1
    content2 = open(html2, "r", encoding="utf-8").read()
    assert "Updated Guide Edition 2" in content2
    assert "Brand New Content" in content2


def test_web_settings_html_file_exists():
    html_path = os.path.join(settings_server.SCRIPT_DIR, "web_settings", "index.html")
    assert os.path.isfile(html_path)
    content = open(html_path, "r", encoding="utf-8").read()
    assert 'data-theme="dark"' in content
    assert "glass-card" in content
    assert "Nemotron" in content or "nemotron_fast" in content
    assert "main_PRE_ROLL_BUFFER_MS" in content
    assert "main_VAD_THRESHOLD" in content
