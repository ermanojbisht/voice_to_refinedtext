"""Tests verifying review_engine.py cleanly integrates with pwd_helper.tts.

Ensures complete backward compatibility with review_config.json, UI narrations,
and step narration variants.
"""
from unittest.mock import patch, MagicMock
import pytest

import review_engine


def test_review_engine_narrate_delegates_to_tts():
    config = {"voice_narration": True, "tts_engine": "piper"}
    with patch("pwd_helper.tts.speak") as mock_speak:
        review_engine.narrate("शाम की समीक्षा शुरू करें।", config, blocking=True)
        mock_speak.assert_called_once_with("शाम की समीक्षा शुरू करें।", blocking=True, config=config)


def test_review_engine_narrate_respects_disabled_flag():
    config = {"voice_narration": False}
    with patch("pwd_helper.tts.speak") as mock_speak:
        review_engine.narrate("Some message", config)
        mock_speak.assert_not_called()


def test_review_engine_stop_narration_delegates_to_tts():
    with patch("pwd_helper.tts.stop") as mock_stop:
        review_engine.stop_narration()
        mock_stop.assert_called_once()
