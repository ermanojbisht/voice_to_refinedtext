"""Tests for TTS CLI arguments and REST API endpoints.

Verifies pwd_cli speech flags, Markdown note speech flags, and settings_server
REST endpoints (/api/tts/speak, /api/tts/stop, /api/tts/status).
"""
import json
import pytest
from unittest.mock import patch, MagicMock

import pwd_cli
import settings_server


def test_pwd_cli_speak_arguments():
    parser = pwd_cli.build_parser()
    
    args = parser.parse_args(["--speak", "Good evening Manoj"])
    assert args.speak == "Good evening Manoj"
    
    args_file = parser.parse_args(["--speak-file", "notes/today.md"])
    assert args_file.speak_file == "notes/today.md"
    
    args_stop = parser.parse_args(["--stop-speech"])
    assert args_stop.stop_speech is True
    
    args_read = parser.parse_args(["--listen", "--read-result"])
    assert args_read.voice is True
    assert args_read.read_result is True


def test_api_tts_status_endpoint():
    with patch("pwd_helper.tts.get_status", return_value={"status": "idle", "backend": "piper"}):
        req = MagicMock()
        req.command = "GET"
        req.path = "/api/tts/status"
        
        status_code, body = settings_server.handle_api_request("/api/tts/status", "GET", None)
        assert status_code == 200
        data = json.loads(body)
        assert data.get("status") == "idle"
        assert data.get("backend") == "piper"


def test_api_tts_speak_endpoint():
    with patch("pwd_helper.tts.speak", return_value=True) as mock_speak:
        status_code, body = settings_server.handle_api_request(
            "/api/tts/speak",
            "POST",
            json.dumps({"text": "Inspection verified.", "blocking": False, "voice": "ni_air_anchor_m"}).encode("utf-8")
        )
        assert status_code == 200
        data = json.loads(body)
        assert data.get("ok") is True
        mock_speak.assert_called_once()
        args, kwargs = mock_speak.call_args
        assert kwargs.get("config", {}).get("voice") == "ni_air_anchor_m"


def test_api_tts_voices_endpoint():
    status_code, body = settings_server.handle_api_request("/api/tts/voices", "GET", None)
    assert status_code == 200
    data = json.loads(body)
    assert data.get("ok") is True
    voices = data.get("voices", [])
    voice_ids = [v["id"] for v in voices]
    assert "ni_delhi_corp_f" in voice_ids
    assert "ni_air_anchor_m" in voice_ids
    assert "ni_docu_deep_m" in voice_ids


def test_pwd_cli_stdin_pipe():
    parser = pwd_cli.build_parser()
    args = parser.parse_args(["--speak", "-"])
    assert args.speak == "-"


def test_api_tts_stop_endpoint():
    with patch("pwd_helper.tts.stop", return_value=True) as mock_stop:
        status_code, body = settings_server.handle_api_request("/api/tts/stop", "POST", None)
        assert status_code == 200
        data = json.loads(body)
        assert data.get("ok") is True
        mock_stop.assert_called_once()
