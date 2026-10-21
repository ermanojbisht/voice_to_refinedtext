"""Abstract Base Class for TTS Backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class BaseTTSBackend(ABC):
    """Abstract interface that every speech backend must implement."""
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if backend executable, libraries, and models are present."""
        pass

    @abstractmethod
    def synthesize_and_play(
        self,
        text: str,
        lang: str = "auto",
        blocking: bool = False,
        speed: float = 1.0,
        config: Mapping[str, Any] | None = None,
    ) -> bool:
        """Synthesize text and play audio. Returns True on success, False on error."""
        pass
