"""Unit and integration tests for Executive Evening Review Web Studio & REST API."""
import base64
import json
import socket
import time
import urllib.request
import urllib.parse
import pytest

from review_service import ReviewService
import review_engine
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


def test_review_service_singleton():
    svc1 = ReviewService.get_instance()
    svc2 = ReviewService.get_instance()
    assert svc1 is svc2
    state = svc1.get_state()
    assert "date" in state
    assert "steps" in state


def test_review_html_page(running_server):
    url = f"http://127.0.0.1:{running_server}/review"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "Executive Evening Review Studio" in content
        assert "stepperBar" in content
        assert "partner-card" in content
        assert "clipList" in content
        assert "noteMarkdownView" in content


def test_review_api_state(running_server):
    url = f"http://127.0.0.1:{running_server}/api/review/state"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "date" in data
        assert "steps" in data
        assert len(data["steps"]) >= 4


def test_review_api_start_advance_cancel(running_server):
    # 1. Start review
    url_start = f"http://127.0.0.1:{running_server}/api/review/start"
    payload = json.dumps({"date": "2026-10-19"}).encode("utf-8")
    req = urllib.request.Request(url_start, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("ok") is True

    # Check active state
    url_state = f"http://127.0.0.1:{running_server}/api/review/state"
    with urllib.request.urlopen(url_state, timeout=2.0) as resp:
        state = json.loads(resp.read().decode("utf-8"))
        assert state.get("active") is True
        assert state.get("current_step_index") == 0

    # 2. Stage clip
    rev_state = review_engine.load_state()
    review_engine.accumulate_clip(rev_state, "Test raw clip for wellness")

    # 3. Update clip
    url_update = f"http://127.0.0.1:{running_server}/api/review/update_clip"
    req = urllib.request.Request(
        url_update,
        data=json.dumps({"index": 0, "text": "Corrected wellness clip"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res.get("ok") is True
        assert any(c["text"] == "Corrected wellness clip" for c in res["state"]["clips"])

    # 4. Note preview
    url_preview = f"http://127.0.0.1:{running_server}/api/review/note_preview"
    with urllib.request.urlopen(url_preview, timeout=2.0) as resp:
        assert resp.status == 200
        preview = json.loads(resp.read().decode("utf-8"))
        assert "content" in preview

    # 5. Cancel review
    url_cancel = f"http://127.0.0.1:{running_server}/api/review/cancel"
    req = urllib.request.Request(url_cancel, data=b"{}", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("ok") is True
