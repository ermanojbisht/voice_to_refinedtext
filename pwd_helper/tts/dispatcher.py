"""Speech Dispatcher — Central Coordinator for Universal TTS."""
from __future__ import annotations

import os
import signal
import subprocess
import threading
from typing import Any, Mapping

from pwd_helper.tts.backends.base import BaseTTSBackend
from pwd_helper.tts.backends.espeak_backend import ESpeakBackend
from pwd_helper.tts.backends.kokoro_backend import KokoroBackend
from pwd_helper.tts.backends.piper_backend import PiperBackend
from pwd_helper.tts.backends.sherpa_backend import SherpaBackend
from pwd_helper.tts.normalizer import clean_for_speech, detect_speech_language

_PID_FILE = "/tmp/pwd_speech.pid"
_LAST_TEXT_FILE = "/tmp/pwd_speech_last.txt"


class SpeechDispatcher:
    """Manages TTS backends, priorities, fallback routing, and playback concurrency."""

    def __init__(self) -> None:
        self._backends: list[tuple[int, BaseTTSBackend]] = []
        self._lock = threading.Lock()
        self._active_proc: subprocess.Popen | None = None
        self._last_spoken_text: str = ""
        self.last_used_backend: str | None = None

        # Register default built-in backends (lower number = higher priority)
        self.register_backend(KokoroBackend(), priority=5)
        self.register_backend(SherpaBackend(), priority=10)
        self.register_backend(PiperBackend(), priority=20)
        self.register_backend(ESpeakBackend(), priority=99)

    def register_backend(self, backend: BaseTTSBackend, priority: int = 50) -> None:
        """Register a backend with a priority (lower number = higher priority)."""
        with self._lock:
            # Replace existing backend with the same name if present
            self._backends = [b for b in self._backends if b[1].name != backend.name]
            self._backends.append((priority, backend))
            self._backends.sort(key=lambda x: x[0])

    def resolve_language(self, text: str) -> str:
        """Determine language for synthesis."""
        return detect_speech_language(text)

    def set_active_proc(self, proc: subprocess.Popen) -> None:
        """Record the active subprocess and write PID file."""
        with self._lock:
            self._active_proc = proc
            try:
                with open(_PID_FILE, "w", encoding="utf-8") as f:
                    f.write(str(proc.pid))
            except Exception:
                pass

    def stop(self) -> None:
        """Stop any active speech playback immediately."""
        with self._lock:
            if self._active_proc:
                try:
                    self._active_proc.terminate()
                except Exception:
                    pass
                self._active_proc = None

            if os.path.exists(_PID_FILE):
                try:
                    with open(_PID_FILE, "r", encoding="utf-8") as f:
                        pid = int(f.read().strip())
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
                try:
                    os.unlink(_PID_FILE)
                except Exception:
                    pass

    def get_last_spoken_text(self) -> str:
        """Return the most recently spoken text."""
        if self._last_spoken_text:
            return self._last_spoken_text
        if os.path.isfile(_LAST_TEXT_FILE):
            try:
                with open(_LAST_TEXT_FILE, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                pass
        return ""

    def speak(
        self,
        text: str,
        lang: str = "auto",
        blocking: bool = False,
        speed: float = 1.0,
        config: Mapping[str, Any] | None = None,
    ) -> bool:
        """Synthesize and play speech, passing through the text normalizer."""
        if not text or not text.strip():
            return False

        # Stop previous playback before starting new one
        self.stop()

        # Resolve language from original input text before markdown/phonetic cleaning
        resolved_lang = self.resolve_language(text) if lang == "auto" else lang

        # Clean markdown, YAML frontmatter, emojis, and expand currency
        cleaned = clean_for_speech(text, lang=resolved_lang)
        if not cleaned:
            return False

        self._last_spoken_text = cleaned
        try:
            with open(_LAST_TEXT_FILE, "w", encoding="utf-8") as f:
                f.write(cleaned)
        except Exception:
            pass

        # Try backends in priority order
        with self._lock:
            candidate_backends = list(self._backends)

        for _, backend in candidate_backends:
            if backend.is_available():
                success = backend.synthesize_and_play(
                    cleaned,
                    lang=resolved_lang,
                    blocking=blocking,
                    speed=speed,
                    config=config,
                )
                if success:
                    self.last_used_backend = backend.name
                    return True

        return False

    def replay(self) -> bool:
        """Replay the last spoken message."""
        last = self.get_last_spoken_text()
        if last:
            return self.speak(last, blocking=False)
        return False

    def get_status(self) -> dict[str, Any]:
        """Return status information for health checks and REST API."""
        with self._lock:
            is_busy = bool(self._active_proc and self._active_proc.poll() is None)
            available = [b.name for _, b in self._backends if b.is_available()]
        return {
            "status": "speaking" if is_busy else "idle",
            "last_used_backend": self.last_used_backend,
            "available_backends": available,
            "last_spoken_text": self._last_spoken_text,
        }


# Global singleton instance
_DISPATCHER_SINGLETON: SpeechDispatcher | None = None


def get_dispatcher() -> SpeechDispatcher:
    global _DISPATCHER_SINGLETON
    if _DISPATCHER_SINGLETON is None:
        _DISPATCHER_SINGLETON = SpeechDispatcher()
    return _DISPATCHER_SINGLETON
