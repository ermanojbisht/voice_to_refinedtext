import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from pwd_helper.secrets import get_secret
import telegram_service


def test_get_secret_from_env(monkeypatch):
    monkeypatch.setenv("TEST_TELEGRAM_TOKEN", "12345:TEST_TOKEN")
    secret = get_secret("telegram_token", env_name="TEST_TELEGRAM_TOKEN")
    assert secret == "12345:TEST_TOKEN"


def test_get_secret_env_pointer_in_config(monkeypatch):
    monkeypatch.setenv("CUSTOM_BOT_KEY", "env_secret_val_999")
    config = {"telegram_bot_token": "env:CUSTOM_BOT_KEY"}
    secret = get_secret("telegram_bot_token", config=config)
    assert secret == "env_secret_val_999"


def test_get_secret_from_secrets_json(tmp_path, monkeypatch):
    secrets_file = tmp_path / ".secrets.json"
    secrets_file.write_text('{"my_key": "json_secret_val"}', encoding="utf-8")
    
    with patch("pwd_helper.secrets._SECRETS_FILE", secrets_file):
        val = get_secret("my_key")
        assert val == "json_secret_val"


def test_get_secret_fallback_to_config():
    config = {"api_key": "direct_config_val"}
    val = get_secret("api_key", config=config)
    assert val == "direct_config_val"


def test_telegram_service_resolution(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token_from_env_777")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat_id_999")
    
    cfg = {"telegram_enabled": True, "telegram_bot_token": "", "telegram_chat_id": ""}
    assert telegram_service.is_configured(cfg) is True
    
    token, chat_id = telegram_service._resolve_credentials(cfg)
    assert token == "token_from_env_777"
    assert chat_id == "chat_id_999"
