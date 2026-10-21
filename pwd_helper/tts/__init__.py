"""Universal Speech Synthesis (TTS) Package.

Modular, low-latency text-to-speech architecture with Indian English (en-IN),
Devanagari Hindi, and Hinglish support, clean Markdown sanitization, and
multi-backend fallback routing.
"""
from __future__ import annotations

from pwd_helper.tts.normalizer import clean_for_speech, detect_speech_language
from pwd_helper.tts.dispatcher import SpeechDispatcher, get_dispatcher

__all__ = [
    "clean_for_speech",
    "detect_speech_language",
    "SpeechDispatcher",
    "get_dispatcher",
    "speak",
    "stop",
    "replay",
    "get_status",
]


def speak(text: str, lang: str = "auto", blocking: bool = False, speed: float = 1.0, config: dict | None = None) -> bool:
    """Convenience function to synthesize and play speech using the default dispatcher."""
    return get_dispatcher().speak(text, lang=lang, blocking=blocking, speed=speed, config=config)


def stop() -> None:
    """Convenience function to immediately interrupt active speech."""
    get_dispatcher().stop()


def replay() -> bool:
    """Convenience function to replay the last spoken text."""
    return get_dispatcher().replay()


def get_status() -> dict:
    """Return status and active backends of the default dispatcher."""
    return get_dispatcher().get_status()
