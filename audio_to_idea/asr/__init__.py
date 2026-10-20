"""Modular ASR subsystem for Voice Refiner and Audio to Ideas.

Provides pluggable backends:
- FasterWhisperProvider (CTranslate2, word-level timestamps)
- TranscribeCppProvider (GGML/Vulkan/CUDA: Nemotron, Voxtral, Whisper .bin/.gguf)
- HandyCliProvider (Headless /usr/bin/handy subprocess fallback)
- ASRFactory (Resilient builder with fallback chains)
"""
from __future__ import annotations

from .base import ASRResult, ASRSegment, ASRWord, BaseASRProvider
from .factory import ASRFactory
from .faster_whisper import FasterWhisperProvider
from .handy_cli import HandyCliProvider
from .transcribe_cpp import TranscribeCppProvider

__all__ = [
    "ASRFactory",
    "ASRResult",
    "ASRSegment",
    "ASRWord",
    "BaseASRProvider",
    "FasterWhisperProvider",
    "HandyCliProvider",
    "TranscribeCppProvider",
]
