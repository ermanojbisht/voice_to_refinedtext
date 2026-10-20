"""Transcribe-CPP (GGML Vulkan / CUDA) implementation of BaseASRProvider.

Powers high-performance local inference for:
- NVIDIA Nemotron 3.5 Streaming (0.6B GGUF) — ~140ms latency on RTX 3060
- Whisper GGML models (.bin and .gguf, including Roman Hinglish Apex)
- Mistral Voxtral Realtime (4B GGUF)
- Moonshine, Parakeet, and Canary GGUF variants
"""
from __future__ import annotations

import gc
import os
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base import ASRResult, ASRSegment, ASRWord, BaseASRProvider

if TYPE_CHECKING:
    import numpy as np


class TranscribeCppProvider(BaseASRProvider):
    """GGML runtime provider using transcribe-cpp Python bindings."""

    def __init__(
        self,
        model_path: str,
        *,
        family: str = "auto",
        device: str = "auto",
        cpu_threads: int = 4,
    ):
        self.model_path = os.path.expanduser(str(model_path))
        self.family = family
        self.requested_device = device
        self.cpu_threads = cpu_threads

        self._model = None
        self._session = None
        self.active_backend = None

    def is_available(self) -> bool:
        """Checks if transcribe_cpp is installed and model file exists."""
        try:
            import transcribe_cpp  # noqa: F401
            return os.path.isfile(self.model_path)
        except (ImportError, Exception):
            return False

    def load(self) -> None:
        """Loads model into GGML Vulkan/CUDA runtime and creates reusable session."""
        if self._model is not None and self._session is not None:
            return

        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(f"ASR Model file not found: {self.model_path}")

        import transcribe_cpp

        self._model = transcribe_cpp.Model(self.model_path)
        self._session = self._model.session()
        self.active_backend = getattr(self._model, "backend", "ggml")

    def _resolve_language(self, language: Optional[str]) -> Optional[str]:
        """Maps ISO 639-1 language code (e.g. 'en', 'hi') to model-supported BCP-47 tag."""
        if not language or not self._model:
            return None
        caps = getattr(self._model, "capabilities", None)
        supported = getattr(caps, "languages", ()) if caps else ()
        if not supported:
            return language
        if language in supported:
            return language
        lang_lower = language.lower().strip()
        for sup in supported:
            if sup.lower().startswith(f"{lang_lower}-") or sup.lower() == lang_lower:
                return sup
        return None

    def transcribe(
        self,
        pcm: np.ndarray,
        *,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        **kwargs: Any
    ) -> ASRResult:
        self.load()
        assert self._session is not None

        t0 = time.perf_counter()
        duration_s = float(len(pcm)) / 16000.0 if len(pcm) > 0 else 0.0

        if len(pcm) == 0:
            return ASRResult(
                text="",
                language=language,
                duration=0.0,
                latency_ms=0.0,
                segments=[],
                backend="transcribe_cpp",
                model_path=self.model_path,
            )

        # Ensure float32 16kHz mono format
        import numpy as np
        if pcm.dtype != np.float32:
            pcm = pcm.astype(np.float32)

        # Normalize int16 range to [-1.0, 1.0] if needed
        max_val = np.max(np.abs(pcm)) if len(pcm) > 0 else 0.0
        if max_val > 1.5:
            pcm = pcm / 32768.0

        run_kwargs = {}
        resolved_lang = self._resolve_language(language)
        if resolved_lang:
            run_kwargs["language"] = resolved_lang
        if prompt:
            run_kwargs["prompt"] = prompt

        try:
            raw_res = self._session.run(pcm, **run_kwargs)
            full_text = getattr(raw_res, "text", str(raw_res)).strip()
        except Exception:
            # If GPU VRAM allocation fails, evict any idle Ollama model from VRAM and retry
            try:
                import requests
                requests.post("http://localhost:11434/api/generate", json={"model": "qwen2.5:3b", "keep_alive": 0}, timeout=1.0)
            except Exception:
                pass
            self._session = self._model.session()
            raw_res = self._session.run(pcm, **run_kwargs)
            full_text = getattr(raw_res, "text", str(raw_res)).strip()

        latency_ms = (time.perf_counter() - t0) * 1000.0

        # Construct segments & approximate proportional word timestamps
        segments: List[ASRSegment] = []
        if full_text:
            words_list: List[ASRWord] = []
            tokens = full_text.split()
            if tokens and duration_s > 0:
                time_per_word = duration_s / max(len(tokens), 1)
                for i, tok in enumerate(tokens):
                    w_start = round(i * time_per_word, 3)
                    w_end = round(min(duration_s, (i + 1) * time_per_word), 3)
                    words_list.append(ASRWord(text=tok, start=w_start, end=w_end, probability=0.99))

            segments.append(
                ASRSegment(
                    id="S00001",
                    text=full_text,
                    start=0.0,
                    end=duration_s,
                    words=words_list,
                    avg_logprob=-0.1,
                    no_speech_prob=0.0,
                )
            )

        detected_lang = getattr(raw_res, "language", language)

        return ASRResult(
            text=full_text,
            language=detected_lang,
            duration=duration_s,
            latency_ms=latency_ms,
            segments=segments,
            backend="transcribe_cpp",
            model_path=self.model_path,
        )

    def close(self) -> None:
        """Releases session and model weights."""
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
            self._session = None

        if self._model is not None:
            try:
                self._model.close()
            except Exception:
                pass
            self._model = None

        self.active_backend = None
        gc.collect()
