"""Core ASR data models and abstract provider interface.

Maintains compatibility across:
- Ubuntu 22.04 (Python 3.10)
- Ubuntu 26.04 (Python 3.14)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import numpy as np


@dataclass
class ASRWord:
    """Represents a single word with source-audio timestamps."""
    text: str
    start: float  # seconds from beginning of audio
    end: float    # seconds from beginning of audio
    probability: float = 1.0  # confidence score [0.0, 1.0]


@dataclass
class ASRSegment:
    """Represents an utterance segment matching audio_to_idea merging conventions."""
    id: str  # e.g., "S00001"
    text: str
    start: float
    end: float
    words: List[ASRWord] = field(default_factory=list)
    avg_logprob: float = 0.0
    no_speech_prob: float = 0.0


@dataclass
class ASRResult:
    """Complete result returned by all ASR providers."""
    text: str                      # Full concatenated transcript
    language: Optional[str]        # Detected or forced ISO language code (e.g. 'en', 'hi')
    duration: float                # Audio duration in seconds
    latency_ms: float              # Wall-clock processing time in milliseconds
    segments: List[ASRSegment]     # List of parsed segments
    backend: str = "unknown"       # Backend provider identifier (e.g. 'faster_whisper', 'transcribe_cpp')
    model_path: str = ""           # Path or identifier of the active model


class BaseASRProvider(ABC):
    """Abstract Base Class for all pluggable speech-to-text engines.

    Lifecycle:
        provider = ASRFactory.from_settings(...)
        provider.load()         # Idempotent: loads weights into RAM/VRAM
        res = provider.transcribe(pcm, ...)  # Process 16kHz float32 mono PCM
        provider.close()        # Release memory when finished (if required)
    """

    @abstractmethod
    def load(self) -> None:
        """Load model weights into memory. Idempotent."""
        pass

    @abstractmethod
    def transcribe(
        self,
        pcm: np.ndarray,
        *,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        **kwargs: Any
    ) -> ASRResult:
        """Transcribe 16 kHz mono float32 PCM audio.

        Args:
            pcm: 1D numpy array of float32 samples in range [-1.0, 1.0].
            language: Optional ISO-639-1 language code (e.g., 'en', 'hi') or None for auto.
            prompt: Optional glossary/context prompt to steer vocabulary.
            kwargs: Backend-specific arguments if needed.

        Returns:
            ASRResult containing transcribed text and segment metadata.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Release loaded model weights and free GPU/system memory. Idempotent."""
        pass

    def is_available(self) -> bool:
        """Check if dependencies/binaries required by this provider are installed."""
        return True
