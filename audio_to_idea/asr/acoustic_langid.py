"""3-Portion Acoustic Language Identification and Suggestion Engine.

Analyzes spoken audio across Start (0s), Middle (50%), and End (80%) portions
using batched Whisper acoustic encoder representations to detect pure English,
pure Hindi, or mixed bilingual code-switching without blocking or auto-switching.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

HINDI_FAMILY = {"hi", "ur", "pa", "mr", "gu", "ne", "sd", "bho"}
ENGLISH_FAMILY = {"en"}


class AcousticLanguageDetector:
    """Thread-safe detector for multi-window acoustic language identification."""

    _instance: Optional["AcousticLanguageDetector"] = None

    @classmethod
    def get_instance(cls, model_size: str = "large-v3-turbo") -> "AcousticLanguageDetector":
        if cls._instance is None:
            cls._instance = cls(model_size=model_size)
        return cls._instance

    def __init__(self, model_size: str = "large-v3-turbo"):
        self.model_size = model_size
        self._model = None
        self._fe = None

    def _ensure_model(self):
        if self._model is not None:
            return self._model, self._fe

        from faster_whisper import WhisperModel
        import ctranslate2

        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        try:
            self._model = WhisperModel(self.model_size, device=device, compute_type=compute_type)
        except Exception:
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        self._fe = self._model.feature_extractor
        return self._model, self._fe

    def detect(
        self,
        audio_input: Union[str, np.ndarray],
        sample_rate: int = 16000,
        slice_duration_s: float = 2.0
    ) -> Dict[str, Any]:
        """Runs 3-slice acoustic language identification.

        Returns:
            dict containing detected_mode, primary_lang, avg_english_score,
            avg_hindi_score, slices metadata, and latency_ms.
        """
        t0 = time.perf_counter()
        
        # Load audio into float32 16kHz mono array
        if isinstance(audio_input, str):
            if not os.path.isfile(audio_input):
                return {
                    "ok": False,
                    "error": f"Audio file not found: {audio_input}",
                    "detected_mode": "unknown"
                }
            import scipy.io.wavfile as wav
            import scipy.signal as signal
            sr, data = wav.read(audio_input)
            if data.dtype == np.int16:
                pcm = data.astype(np.float32) / 32768.0
            else:
                pcm = data.astype(np.float32)
            if len(pcm.shape) > 1:
                pcm = pcm.mean(axis=1)
            if sr != 16000 and len(pcm) > 0:
                pcm = signal.resample(pcm, int(len(pcm) * 16000 / sr))
        else:
            pcm = np.asarray(audio_input, dtype=np.float32)
            if len(pcm.shape) > 1:
                pcm = pcm.mean(axis=1)

        total_samples = len(pcm)
        if total_samples < 4000:  # < 0.25s of audio
            return {
                "ok": True,
                "detected_mode": "pure_english",
                "primary_lang": "en",
                "avg_english_score": 1.0,
                "avg_hindi_score": 0.0,
                "slices": [],
                "latency_ms": 0.0
            }

        # Trim lead-in silence by finding energy > threshold
        energy = np.abs(pcm)
        speech_indices = np.where(energy > 0.015)[0]
        start_sample = int(speech_indices[0]) if len(speech_indices) > 0 else 0
        active_pcm = pcm[start_sample:]
        active_samples = len(active_pcm)

        slice_samples = int(16000 * slice_duration_s)
        if active_samples <= slice_samples:
            # Short audio: single slice
            slice_offsets = [(0, "start")]
        else:
            # 3 slices: start (0s), middle (50%), end (80%)
            mid_sample = int(active_samples * 0.5)
            end_sample = int(active_samples * 0.8)
            slice_offsets = [
                (0, "start"),
                (mid_sample, "middle"),
                (end_sample, "end")
            ]

        raw_slices = []
        slice_meta = []
        for offset, pos in slice_offsets:
            s = active_pcm[offset : offset + slice_samples]
            if len(s) < 1600:  # pad if tiny
                s = np.pad(s, (0, 1600 - len(s)))
            raw_slices.append(s)
            slice_meta.append({
                "position": pos,
                "time_offset_s": round((start_sample + offset) / 16000.0, 2)
            })

        model, fe = self._ensure_model()
        from faster_whisper.audio import pad_or_trim
        import ctranslate2

        feats = [pad_or_trim(fe(s), fe.nb_max_frames) for s in raw_slices]
        batch = np.stack(feats, axis=0)
        storage = ctranslate2.StorageView.from_array(batch)

        try:
            encoded = model.model.encode(storage)
        except RuntimeError as e:
            if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                self._fe = self._model.feature_extractor
                model = self._model
                storage = ctranslate2.StorageView.from_array(batch)
                encoded = model.model.encode(storage)
            else:
                raise
        results = model.model.detect_language(encoded)

        en_scores = []
        hi_scores = []
        slices_out = []

        for i, res in enumerate(results):
            probs = {t[2:-2]: p for t, p in res}
            p_en = probs.get("en", 0.0)
            p_hi = sum(probs.get(k, 0.0) for k in HINDI_FAMILY)
            en_scores.append(p_en)
            hi_scores.append(p_hi)
            
            top_lang = res[0][0][2:-2] if res else "en"
            meta = slice_meta[i]
            meta.update({
                "p_en": round(float(p_en), 2),
                "p_hi": round(float(p_hi), 2),
                "top_lang": top_lang
            })
            slices_out.append(meta)

        avg_en = float(np.mean(en_scores))
        avg_hi = float(np.mean(hi_scores))

        # Classification heuristics based on multi-slice consistency
        has_english_slice = any(s["p_en"] >= 0.30 or s["top_lang"] == "en" for s in slices_out)
        has_hindi_slice = any(s["p_hi"] >= 0.30 or s["top_lang"] in HINDI_FAMILY for s in slices_out)

        if has_english_slice and has_hindi_slice:
            detected_mode = "mixed_bilingual"
            primary_lang = "en" if avg_en >= avg_hi else "hi"
        elif has_english_slice and not has_hindi_slice and avg_en >= 0.70:
            detected_mode = "pure_english"
            primary_lang = "en"
        elif has_hindi_slice and not has_english_slice and avg_hi >= 0.60:
            detected_mode = "pure_hindi"
            primary_lang = "hi"
        else:
            detected_mode = "mixed_bilingual"
            primary_lang = "en" if avg_en >= avg_hi else "hi"

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        return {
            "ok": True,
            "detected_mode": detected_mode,
            "primary_lang": primary_lang,
            "avg_english_score": round(avg_en, 2),
            "avg_hindi_score": round(avg_hi, 2),
            "slices": slices_out,
            "latency_ms": latency_ms
        }


def get_acoustic_suggestion(
    detected_info: Dict[str, Any],
    current_preset: str
) -> Optional[Dict[str, Any]]:
    """Evaluates whether current ASR preset matches acoustics, returning advisory suggestion."""
    if not detected_info or not detected_info.get("ok"):
        return None

    # smart_bilingual handles all audio (English, Hindi, and mixed) natively without conflict
    if current_preset == "smart_bilingual":
        return None

    detected_mode = detected_info.get("detected_mode", "unknown")
    avg_en = detected_info.get("avg_english_score", 0.0)
    avg_hi = detected_info.get("avg_hindi_score", 0.0)

    if current_preset == "instant_english":
        if detected_mode == "pure_hindi":
            return {
                "is_mismatch": True,
                "severity": "warning",
                "suggested_preset": "instant_hindi",
                "alternative_preset": "smart_bilingual",
                "title": "Hindi Speech Detected",
                "message": (
                    f"Acoustic analysis detected Hindi speech ({int(avg_hi*100)}% Hindi phonemes). "
                    "Instant English may produce distorted words. Consider switching to Instant Hindi or Smart Bilingual."
                ),
                "detected_mode": detected_mode
            }
        elif detected_mode == "mixed_bilingual":
            return {
                "is_mismatch": True,
                "severity": "suggestion",
                "suggested_preset": "smart_bilingual",
                "alternative_preset": "instant_english",
                "title": "Mixed Hindi & English Detected",
                "message": (
                    "Acoustic analysis detected code-mixed speech (Hindi + English). "
                    "If technical terms or sentences appear garbled, consider switching to Smart Bilingual."
                ),
                "detected_mode": detected_mode
            }

    elif current_preset == "instant_hindi":
        if detected_mode == "pure_english":
            return {
                "is_mismatch": True,
                "severity": "warning",
                "suggested_preset": "instant_english",
                "alternative_preset": "smart_bilingual",
                "title": "English Speech Detected",
                "message": (
                    f"Acoustic analysis detected English speech ({int(avg_en*100)}% English phonemes). "
                    "Instant Hindi may force English into phonetic Devanagari. Consider switching to Instant English."
                ),
                "detected_mode": detected_mode
            }
        elif detected_mode == "mixed_bilingual":
            return {
                "is_mismatch": True,
                "severity": "suggestion",
                "suggested_preset": "smart_bilingual",
                "alternative_preset": "instant_hindi",
                "title": "Mixed English & Hindi Detected",
                "message": (
                    "Acoustic analysis detected mixed speech. "
                    "For clean preservation of English technical acronyms alongside Hindi, consider Smart Bilingual."
                ),
                "detected_mode": detected_mode
            }

    elif current_preset == "roman_hinglish":
        if detected_mode == "pure_english":
            return {
                "is_mismatch": False,
                "severity": "info",
                "suggested_preset": "instant_english",
                "title": "Pure English Speech",
                "message": (
                    "Audio is purely English. Instant English (<0.8s) would offer faster processing without script difference."
                ),
                "detected_mode": detected_mode
            }

    return None
