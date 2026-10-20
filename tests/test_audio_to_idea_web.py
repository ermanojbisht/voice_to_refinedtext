"""Unit and integration tests for Audio-to-Ideas Web Service & REST API."""
import json
import os
import socket
import time
import urllib.request
import urllib.parse
from pathlib import Path
import pytest

from audio_to_idea.web_service import AudioIdeaWebService
from audio_to_idea.templates import MODES
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


def test_web_service_state():
    svc = AudioIdeaWebService.get_instance()
    assert svc.settings is not None
    assert isinstance(svc.items, list)
    profiles = svc.get_profiles()
    assert len(profiles) >= 1
    assert any(p["label"] == "No profile" for p in profiles)


def test_web_service_queue_ops(tmp_path):
    svc = AudioIdeaWebService.get_instance()
    svc.clear_queue()
    assert len(svc.items) == 0

    # Create dummy audio files
    f1 = tmp_path / "rec1.wav"
    f2 = tmp_path / "rec2.mp3"
    f1.write_bytes(b"RIFFdummywavdata")
    f2.write_bytes(b"ID3dummymp3data")

    added = svc.add_paths([str(f1), str(f2)])
    assert len(added) == 2
    assert len(svc.items) == 2
    assert svc.selected_id == added[0]["id"]

    # Test removing one item
    item1_id = added[0]["id"]
    removed = svc.remove_item(item1_id)
    assert removed is True
    assert len(svc.items) == 1
    assert svc.selected_id == added[1]["id"]

    # Test clearing
    svc.clear_queue()
    assert len(svc.items) == 0


def test_web_service_prompts():
    svc = AudioIdeaWebService.get_instance()
    for mode in MODES:
        info = svc.get_prompt_info(mode)
        assert info["mode"] == mode
        assert "{transcript}" in info["text"]
        assert len(info["builtin_text"]) > 0

    # Test preview prompt
    preview = svc.preview_prompt("clean_paragraph", "Template says: {transcript} [Lang: {output_language}]")
    assert "Template says:" in preview
    assert "sample recording" in preview


def test_web_service_prompt_save_safety(tmp_path):
    svc = AudioIdeaWebService.get_instance()
    # Should reject saving inside builtins or package dir
    from audio_to_idea.templates import BUILTINS
    with pytest.raises(ValueError, match="Choose a separate custom prompt folder"):
        svc.save_prompt("clean_paragraph", "Test {transcript}", custom_folder=str(BUILTINS))

    # Should succeed saving in an allowed external folder
    custom_dir = tmp_path / "custom_prompts"
    res = svc.save_prompt("clean_paragraph", "Custom template: {transcript}", custom_folder=str(custom_dir))
    assert res["ok"] is True
    assert Path(res["path"]).is_file()


def test_http_api_state(running_server):
    url = f"http://127.0.0.1:{running_server}/api/audio_to_idea/state"
    with urllib.request.urlopen(url, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "items" in data
        assert "modes" in data
        assert "profiles" in data
        assert "settings" in data


def test_http_api_prompt_and_preview(running_server):
    # GET prompt info
    url = f"http://127.0.0.1:{running_server}/api/audio_to_idea/prompt?mode=ideas_actions"
    with urllib.request.urlopen(url, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["mode"] == "ideas_actions"
        assert "{transcript}" in data["text"]

    # POST prompt preview
    prev_url = f"http://127.0.0.1:{running_server}/api/audio_to_idea/prompt/preview"
    req_data = json.dumps({
        "mode": "concise_summary",
        "text": "Summarize briefly: {transcript}"
    }).encode("utf-8")
    req = urllib.request.Request(prev_url, data=req_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["ok"] is True
        assert "Summarize briefly:" in data["preview"]


def test_http_api_audio_stream_with_range(running_server, tmp_path):
    # Create test audio file
    dummy_wav = tmp_path / "test_stream.wav"
    dummy_bytes = b"RIFF" + b"X" * 1024
    dummy_wav.write_bytes(dummy_bytes)

    quoted_path = urllib.parse.quote(str(dummy_wav))
    url = f"http://127.0.0.1:{running_server}/api/audio_to_idea/audio_stream?path={quoted_path}"

    # Full request
    with urllib.request.urlopen(url, timeout=3.0) as resp:
        assert resp.status == 200
        assert resp.headers.get("Accept-Ranges") == "bytes"
        assert int(resp.headers.get("Content-Length")) == len(dummy_bytes)
        body = resp.read()
        assert body == dummy_bytes

    # Partial range request (bytes 0-9)
    req = urllib.request.Request(url, headers={"Range": "bytes=0-9"})
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        assert resp.status == 206
        assert resp.headers.get("Content-Range") == f"bytes 0-9/{len(dummy_bytes)}"
        assert int(resp.headers.get("Content-Length")) == 10
        body = resp.read()
        assert body == dummy_bytes[:10]


def test_audio_to_idea_html_endpoint(running_server):
    url = f"http://127.0.0.1:{running_server}/audio-to-idea"
    with urllib.request.urlopen(url, timeout=3.0) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "Audio to Ideas" in content
        assert "dropzone" in content
        assert "audioElement" in content
        assert "evidence-badge" in content
        assert "liveBadge" in content


def test_api_item_add_select_and_detail(running_server, tmp_path):
    # Add dummy audio
    dummy = tmp_path / "meeting_notes.wav"
    dummy.write_bytes(b"RIFF" + b"Y" * 512)

    add_url = f"http://127.0.0.1:{running_server}/api/audio_to_idea/add"
    req_data = json.dumps({"paths": [str(dummy)]}).encode("utf-8")
    req = urllib.request.Request(add_url, data=req_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["ok"] is True
        assert data["added_count"] >= 1

    # Select the added item
    state_url = f"http://127.0.0.1:{running_server}/api/audio_to_idea/state"
    with urllib.request.urlopen(state_url, timeout=3.0) as resp:
        state = json.loads(resp.read().decode("utf-8"))
        assert len(state["items"]) >= 1
        item_id = state["items"][-1]["id"]

    detail_url = f"http://127.0.0.1:{running_server}/api/audio_to_idea/item_detail?id={item_id}"
    with urllib.request.urlopen(detail_url, timeout=3.0) as resp:
        assert resp.status == 200
        detail = json.loads(resp.read().decode("utf-8"))
        assert detail["item"]["id"] == item_id
        assert "audio_url" in detail

