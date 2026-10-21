"""Tests for the Universal TTS Dispatcher & Backend Routing.

Verifies multi-backend resolution, fallback chains, process locking,
interruption capabilities, and language routing.
"""
import os
import subprocess
from unittest.mock import MagicMock, patch
import pytest

from pwd_helper.tts.dispatcher import SpeechDispatcher
from pwd_helper.tts.backends.base import BaseTTSBackend


class DummySuccessBackend(BaseTTSBackend):
    name = "dummy_success"

    def is_available(self) -> bool:
        return True

    def synthesize_and_play(self, text: str, lang: str = "auto", blocking: bool = False, speed: float = 1.0, config=None) -> bool:
        return True


class DummyFailingBackend(BaseTTSBackend):
    name = "dummy_failing"

    def is_available(self) -> bool:
        return True

    def synthesize_and_play(self, text: str, lang: str = "auto", blocking: bool = False, speed: float = 1.0, config=None) -> bool:
        return False


def test_dispatcher_fallback_chain():
    dispatcher = SpeechDispatcher()
    failing = DummyFailingBackend()
    success = DummySuccessBackend()
    
    dispatcher.register_backend(failing, priority=1)
    dispatcher.register_backend(success, priority=2)
    
    res = dispatcher.speak("Test speech fallback", blocking=True)
    assert res is True
    assert dispatcher.last_used_backend == "dummy_success"


def test_dispatcher_tracks_last_spoken_text():
    dispatcher = SpeechDispatcher()
    success = DummySuccessBackend()
    dispatcher.register_backend(success, priority=1)
    
    dispatcher.speak("Important site instructions for junior engineers.", blocking=True)
    assert dispatcher.get_last_spoken_text() == "Important site instructions for junior engineers."


def test_dispatcher_stop_narration(tmp_path):
    dispatcher = SpeechDispatcher()
    mock_proc = MagicMock()
    dispatcher._active_proc = mock_proc
    
    dispatcher.stop()
    mock_proc.terminate.assert_called_once()
    assert dispatcher._active_proc is None


def test_dispatcher_script_routing():
    dispatcher = SpeechDispatcher()
    # Pure devanagari
    assert dispatcher.resolve_language("यह कार्य प्रगति पर है।") == "hi"
    # Pure english
    assert dispatcher.resolve_language("The foundation work is complete.") == "en"


def test_kokoro_backend_detection():
    from pwd_helper.tts.backends.kokoro_backend import KokoroBackend
    backend = KokoroBackend()
    assert backend.is_available() is True
