"""Unit and integration tests for PWD Terminology & SOR Lookup Web Screen."""
import json
import socket
import time
import urllib.request
import pytest

from pwd_service import PWDService
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


def test_pwd_service_terms():
    svc = PWDService.get_instance()
    terms = svc.get_terms()
    assert len(terms) >= 30
    first = terms[0]
    assert "abbr" in first
    assert "english" in first
    assert "category" in first


def test_pwd_service_search():
    svc = PWDService.get_instance()
    results = svc.search("EE")
    assert any(r["abbr"] == "EE" for r in results)

    # Search by category
    doc_results = svc.search("", category="documents")
    assert all(r["category"] == "documents" for r in doc_results)
    assert any(r["abbr"] == "MB" for r in doc_results)


def test_pwd_service_add_custom():
    svc = PWDService.get_instance()
    term = "TEST_ACRONYM_" + str(int(time.time()))
    res = svc.add_custom_term(term, "Test Acronym Meaning English", "टेस्ट परिवर्णी शब्द")
    assert res["term"] == term
    assert res["meaning_en"] == "Test Acronym Meaning English"

    found = svc.search(term)
    assert len(found) == 1
    assert found[0]["english"] == "Test Acronym Meaning English"


def test_pwd_service_translate():
    svc = PWDService.get_instance()
    out = svc.translate_text("The EE signed the MB today.")
    assert "Executive Engineer" in out["en"]
    assert "Measurement Book" in out["en"]
    assert "hi" in out


def test_pwd_html_page(running_server):
    url = f"http://127.0.0.1:{running_server}/pwd-lookup"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "PWD Terminology & SOR Explorer" in content
        assert "searchInput" in content
        assert "termsGrid" in content
        assert "Add Custom Term" in content
        assert "Translation Sandbox" in content


def test_pwd_api_terms(running_server):
    url = f"http://127.0.0.1:{running_server}/api/pwd/terms"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "terms" in data
        assert "categories" in data
        assert len(data["terms"]) >= 30
        assert any(c.lower() == "officers" for c in data["categories"])


def test_pwd_api_search(running_server):
    url = f"http://127.0.0.1:{running_server}/api/pwd/search"
    payload = json.dumps({"query": "MB", "category": "All"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "terms" in data
        assert any(r["abbr"] == "MB" for r in data["terms"])


def test_pwd_api_add_custom(running_server):
    url = f"http://127.0.0.1:{running_server}/api/pwd/add_custom"
    term = "API_TEST_" + str(int(time.time()))
    payload = json.dumps({
        "abbr": term,
        "english": "API Test Term",
        "hindi": "एपीआई टेस्ट",
        "category": "custom"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("ok") is True
        assert data["abbr"] == term


def test_pwd_api_translate(running_server):
    url = f"http://127.0.0.1:{running_server}/api/pwd/translate"
    payload = json.dumps({"text": "The SE inspected the site."}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "result" in data
        assert "normalized" in data["result"]
        assert "Superintending Engineer" in data["result"]["normalized"]
