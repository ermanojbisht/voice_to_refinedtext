from __future__ import annotations
import json
import pytest
from unittest.mock import patch, MagicMock

import utils
from engine import VoiceEngine


def test_call_ollama_includes_keep_alive():
    """Verify call_ollama serializes keep_alive into the POST JSON payload."""
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Refined text here"}
        mock_post.return_value = mock_resp

        res = utils.call_ollama(
            host="http://localhost:11434",
            model="qwen2.5:3b",
            prompt="Hello world",
            stop_tokens=[],
            keep_alive="60m"
        )

        assert res.get("response") == "Refined text here"
        mock_post.assert_called_once()
        sent_json = mock_post.call_args[1]["json"]
        assert sent_json.get("keep_alive") == "60m"
        assert sent_json.get("model") == "qwen2.5:3b"


def test_call_ollama_default_keep_alive():
    """Verify call_ollama defaults to '5m' keep_alive when omitted."""
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "OK"}
        mock_post.return_value = mock_resp

        utils.call_ollama("http://localhost:11434", "test-model", "hi", [])
        sent_json = mock_post.call_args[1]["json"]
        assert sent_json.get("keep_alive") == "5m"


def test_call_ollama_zero_keep_alive_for_low_vram():
    """Verify keep_alive='0' is passed to trigger immediate VRAM eviction."""
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "OK"}
        mock_post.return_value = mock_resp

        utils.call_ollama("http://localhost:11434", "test-model", "hi", [], keep_alive="0")
        sent_json = mock_post.call_args[1]["json"]
        assert sent_json.get("keep_alive") == "0"


def test_engine_refine_passes_configured_keep_alive(tmp_path):
    """Verify VoiceEngine.refine reads OLLAMA_KEEP_ALIVE from config."""
    cfg = {
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_MODELS": {"en": "qwen2.5:3b", "hi": "qwen2.5:3b"},
        "OLLAMA_KEEP_ALIVE": "15m",
        "TEMPERATURE": 0.1,
        "MODE": "refine"
    }
    with patch("utils.load_config", return_value=cfg):
        engine = VoiceEngine(str(tmp_path))

    with patch("utils.call_ollama") as mock_call:
        mock_call.return_value = {"response": "Refined output"}
        with patch.object(engine, "log"):
            res = engine.refine("Raw test text")
            assert res == "Refined output"

        mock_call.assert_called_once()
        assert mock_call.call_args[1]["keep_alive"] == "15m"
