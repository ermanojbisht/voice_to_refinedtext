"""Neural Voice Activity Detection (VAD) module using Silero VAD v6 ONNX."""
import os
import threading
from typing import List, Dict, Any, Optional
import numpy as np


class SileroVAD:
    """Thread-safe neural VAD engine with fallback to energy-based RMS thresholding."""

    _instance: Optional["SileroVAD"] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "SileroVAD":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self, threshold: float = 0.50, neg_threshold: float = 0.35):
        self.threshold = threshold
        self.neg_threshold = neg_threshold
        self._model = None
        self._load_lock = threading.Lock()
        self._load_model()

    def _load_model(self) -> None:
        """Loads SileroVADModel from faster_whisper or local ONNX assets."""
        with self._load_lock:
            try:
                import faster_whisper.vad as f_vad
                self._model = f_vad.get_vad_model()
            except Exception as e:
                # Graceful fallback: model remains None, RMS will be used
                print(f"[SileroVAD] Notice: Neural VAD model unavailable ({e}), falling back to RMS energy.")
                self._model = None

    @property
    def is_neural_available(self) -> bool:
        return self._model is not None

    def speech_probability(self, chunk: np.ndarray) -> float:
        """Evaluates speech probability for a given audio chunk (16kHz float32 mono).

        Returns a float between 0.0 and 1.0. If neural VAD is unavailable,
        maps RMS energy against standard threshold.
        """
        if chunk is None or len(chunk) == 0:
            return 0.0

        if chunk.dtype == np.int16:
            pcm = chunk.astype(np.float32) / 32768.0
        else:
            pcm = chunk.astype(np.float32)

        if len(pcm.shape) > 1:
            pcm = pcm.mean(axis=1)

        if self._model is not None:
            try:
                # Silero requires chunk size to be a multiple of 512
                n_samples = len(pcm)
                valid_len = (n_samples // 512) * 512
                if valid_len == 0:
                    # Pad to 512 if too short
                    padded = np.zeros(512, dtype=np.float32)
                    padded[:n_samples] = pcm
                    out = self._model(padded)
                    return float(np.max(out))

                slice_pcm = pcm[:valid_len]
                out = self._model(slice_pcm)
                return float(np.max(out)) if len(out) > 0 else 0.0
            except Exception:
                pass

        # Fallback to RMS energy thresholding
        rms = float(np.sqrt(np.mean(pcm ** 2)))
        # Map 300/32768 ~= 0.009 to prob 0.5
        prob = min(1.0, rms / 0.02)
        return prob

    def is_speech(self, chunk: np.ndarray, threshold: Optional[float] = None) -> bool:
        """Returns True if the chunk is classified as human speech."""
        t = threshold if threshold is not None else self.threshold
        return self.speech_probability(chunk) >= t

    def get_speech_timestamps(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 250,
    ) -> List[Dict[str, int]]:
        """Extracts speech segments [{'start': sample_idx, 'end': sample_idx}] from full audio."""
        if audio is None or len(audio) == 0:
            return []

        if audio.dtype == np.int16:
            pcm = audio.astype(np.float32) / 32768.0
        else:
            pcm = audio.astype(np.float32)

        if len(pcm.shape) > 1:
            pcm = pcm.mean(axis=1)

        try:
            import faster_whisper.vad as f_vad
            from faster_whisper.vad import VadOptions

            vad_opts = VadOptions(
                threshold=self.threshold,
                min_speech_duration_ms=min_speech_duration_ms,
                min_silence_duration_ms=min_silence_duration_ms,
                speech_pad_ms=max(30, min(100, min_silence_duration_ms // 4)),
            )
            return f_vad.get_speech_timestamps(pcm, vad_opts)
        except Exception:
            # Fallback simple RMS voice envelope
            frame_len = int(sample_rate * 0.032)  # 32ms
            energy = [
                np.sqrt(np.mean(pcm[i : i + frame_len] ** 2))
                for i in range(0, len(pcm) - frame_len, frame_len)
            ]
            thresh = 0.009
            speech = False
            start = 0
            segments = []
            for idx, e in enumerate(energy):
                t_idx = idx * frame_len
                if e >= thresh and not speech:
                    speech = True
                    start = t_idx
                elif e < thresh and speech:
                    speech = False
                    if t_idx - start >= int(sample_rate * min_speech_duration_ms / 1000):
                        segments.append({"start": start, "end": t_idx})
            if speech and len(pcm) - start >= int(sample_rate * min_speech_duration_ms / 1000):
                segments.append({"start": start, "end": len(pcm)})
            return segments
