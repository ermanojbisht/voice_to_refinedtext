"""Faster-Whisper (CTranslate2) implementation of BaseASRProvider.

Preserves:
- Full multilingual speech-to-text accuracy
- Accurate token- and word-level timestamps (for audio_to_idea citations)
- GPU (CUDA) and CPU execution with graceful fallback
- Hindi / Devanagari script steering if requested
"""
from __future__ import annotations

import gc
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base import ASRResult, ASRSegment, ASRWord, BaseASRProvider

if TYPE_CHECKING:
    import numpy as np


class FasterWhisperProvider(BaseASRProvider):
    """Wrapper around faster-whisper CTranslate2 WhisperModel."""

    def __init__(
        self,
        model_path_or_id: str = "large-v3-turbo",
        *,
        device: str = "auto",
        compute_type: str = "auto",
        cpu_threads: int = 4,
        word_timestamps: bool = True,
        offline: bool = True,
    ):
        self.model_path_or_id = model_path_or_id
        self.requested_device = device
        self.requested_compute = compute_type
        self.cpu_threads = cpu_threads
        self.word_timestamps = word_timestamps
        self.offline = offline

        self._model = None
        self.active_device = None
        self.active_compute = None

    def is_available(self) -> bool:
        try:
            import faster_whisper
            return True
        except ImportError:
            return False

    def load(self) -> None:
        """Loads WhisperModel into RAM/VRAM if not already loaded."""
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        # Resolve execution device and compute type
        device = self.requested_device
        compute = self.requested_compute

        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                try:
                    import ctranslate2
                    device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
                except Exception:
                    device = "cpu"

        if compute == "auto":
            compute = "float16" if device == "cuda" else "int8"

        try:
            self._model = WhisperModel(
                self.model_path_or_id,
                device=device,
                compute_type=compute,
                cpu_threads=self.cpu_threads,
            )
            self.active_device = device
            self.active_compute = compute
        except Exception as exc:
            # Fallback to CPU if CUDA initialization fails on requested 'auto'
            if self.requested_device == "auto" and device == "cuda":
                device = "cpu"
                compute = "int8"
                self._model = WhisperModel(
                    self.model_path_or_id,
                    device=device,
                    compute_type=compute,
                    cpu_threads=self.cpu_threads,
                )
                self.active_device = device
                self.active_compute = compute
            else:
                raise

    def transcribe(
        self,
        pcm: np.ndarray,
        *,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        **kwargs: Any
    ) -> ASRResult:
        self.load()
        assert self._model is not None

        t0 = time.perf_counter()
        duration_s = float(len(pcm)) / 16000.0 if len(pcm) > 0 else 0.0

        if len(pcm) == 0:
            return ASRResult(
                text="",
                language=language,
                duration=0.0,
                latency_ms=0.0,
                segments=[],
                backend="faster_whisper",
                model_path=str(self.model_path_or_id),
            )

        vad_filter = kwargs.get("vad_filter", True)
        beam_size = kwargs.get("beam_size", 5)

        raw_segments, info = self._model.transcribe(
            pcm,
            language=language,
            word_timestamps=self.word_timestamps,
            condition_on_previous_text=False,
            vad_filter=vad_filter,
            beam_size=beam_size,
            initial_prompt=prompt[:2000] if prompt else None,
        )

        segments: List[ASRSegment] = []
        full_text_parts: List[str] = []

        seg_idx = 1
        for seg in raw_segments:
            seg_text = seg.text.strip()
            if not seg_text:
                continue

            words: List[ASRWord] = []
            if getattr(seg, "words", None):
                for w in seg.words:
                    words.append(
                        ASRWord(
                            text=w.word,
                            start=w.start,
                            end=w.end,
                            probability=getattr(w, "probability", 1.0),
                        )
                    )

            segments.append(
                ASRSegment(
                    id=f"S{seg_idx:05d}",
                    text=seg_text,
                    start=seg.start,
                    end=seg.end,
                    words=words,
                    avg_logprob=getattr(seg, "avg_logprob", 0.0),
                    no_speech_prob=getattr(seg, "no_speech_prob", 0.0),
                )
            )
            full_text_parts.append(seg_text)
            seg_idx += 1

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return ASRResult(
            text=" ".join(full_text_parts),
            language=getattr(info, "language", language),
            duration=duration_s,
            latency_ms=latency_ms,
            segments=segments,
            backend="faster_whisper",
            model_path=str(self.model_path_or_id),
        )

    def close(self) -> None:
        """Release Whisper model from GPU/RAM."""
        self._model = None
        self.active_device = None
        self.active_compute = None
        gc.collect()
