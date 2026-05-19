#!/usr/bin/env python3
"""Telegram notification service — pluggable module for sending messages to a Telegram chat.

Usage (from any script):
    import telegram_service
    telegram_service.send("Hello!", config)

Config keys (in review_config.json):
    telegram_enabled   : true / false
    telegram_bot_token : token from @BotFather
    telegram_chat_id   : your personal chat ID

The module is intentionally self-contained — no project-specific imports.
It can be dropped into any future project without modification.
"""
import sys

_API_BASE = "https://api.telegram.org/bot{token}/{method}"

# Optional callback set by the host project to route logs through its log file.
# If not set, warnings are printed to stderr.
_log_callback = None


def set_logger(fn):
    """Register a log callback, e.g. telegram_service.set_logger(review_engine._rlog)."""
    global _log_callback
    _log_callback = fn


def _log(msg):
    if _log_callback:
        _log_callback(msg)
    else:
        print(msg, file=sys.stderr)


def _post(token, method, payload, timeout=10):
    """POST payload to a Telegram Bot API method. Returns parsed JSON response."""
    import requests
    url = _API_BASE.format(token=token, method=method)
    resp = requests.post(url, data=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def is_configured(config):
    """Return True if Telegram is enabled and credentials look valid."""
    token = config.get("telegram_bot_token", "").strip()
    chat_id = config.get("telegram_chat_id", "").strip()
    return (
        config.get("telegram_enabled", False)
        and bool(token)
        and bool(chat_id)
        and token != "YOUR_BOT_TOKEN_HERE"
        and chat_id != "YOUR_CHAT_ID_HERE"
    )


def send(text, config):
    """Send a plain-text message. Silently skips if not configured or network fails.

    Returns True on success, False on failure.
    """
    if not is_configured(config):
        return False
    token   = config["telegram_bot_token"].strip()
    chat_id = config["telegram_chat_id"].strip()
    try:
        resp = _post(token, "sendMessage", {"chat_id": chat_id, "text": text})
        if resp.get("ok"):
            _log(f"telegram: sent ok (message_id={resp['result']['message_id']})")
            return True
        _log(f"telegram: API error: {resp.get('description', resp)}")
        return False
    except Exception as exc:
        _log(f"telegram: send failed: {exc}")
        return False


def test_connection(config):
    """Verify credentials by calling getMe. Returns (ok: bool, message: str)."""
    if not config.get("telegram_bot_token", "").strip():
        return False, "Bot token is empty."
    if not config.get("telegram_chat_id", "").strip():
        return False, "Chat ID is empty."
    token   = config["telegram_bot_token"].strip()
    chat_id = config["telegram_chat_id"].strip()
    try:
        me = _post(token, "getMe", {})
        if not me.get("ok"):
            return False, f"Bot token rejected: {me.get('description', 'unknown error')}"
        bot_name = me["result"].get("username", "unknown")
        resp = _post(token, "sendMessage",
                     {"chat_id": chat_id, "text": f"✅ Test from AI Voice Refiner (@{bot_name})"})
        if resp.get("ok"):
            return True, f"Connected as @{bot_name}. Test message sent."
        return False, f"Could not send to chat {chat_id}: {resp.get('description', 'unknown error')}"
    except Exception as exc:
        return False, str(exc)
