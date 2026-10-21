"""Kokoro ONNX Neural TTS Backend — Ultra-low latency CPU speech with Indian English blending."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Mapping

from pwd_helper.tts.backends.base import BaseTTSBackend

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def blend_norm_preserving(kokoro, recipe: dict[str, float]):
    """Blends multiple Kokoro style tensors preserving L2 norm (magnitude) across positions."""
    import numpy as np
    blended = None
    target_norm = None

    for voice_name, weight in recipe.items():
        vec = kokoro.get_voice_style(voice_name).astype(np.float32)
        if blended is None:
            blended = np.zeros_like(vec)
            target_norm = np.zeros((vec.shape[0], 1, 1), dtype=np.float32)
        blended += vec * weight
        target_norm += np.linalg.norm(vec, axis=-1, keepdims=True) * weight

    current_norm = np.linalg.norm(blended, axis=-1, keepdims=True) + 1e-8
    return (blended / current_norm) * target_norm


class KokoroBackend(BaseTTSBackend):
    name = "kokoro"

    def __init__(self) -> None:
        self._kokoro_instance = None
        self._model_path: Path | None = None
        self._voices_path: Path | None = None
        self._blended_en_in_style = None
        self._presets: dict[str, Any] = {}

    def _find_model_paths(self, config: Mapping[str, Any] | None = None) -> tuple[Path | None, Path | None]:
        cfg = config or {}
        custom_dir = cfg.get("kokoro_model_dir")
        candidates = []
        if custom_dir:
            candidates.append(Path(custom_dir).expanduser())

        candidates.extend([
            Path("/media/manoj/F1/mkbmodel/kokoro-models"),
            _REPO_ROOT / "models" / "kokoro-models",
            _REPO_ROOT / "models" / "kokoro",
            Path.home() / ".cache" / "kokoro",
        ])

        for c in candidates:
            if c.is_dir():
                # Prefer int8 for speed, fallback to fp32
                int8_model = c / "kokoro-v1.0.int8.onnx"
                fp32_model = c / "kokoro-v1.0.onnx"
                voices = c / "voices-v1.0.bin"

                model_file = int8_model if int8_model.is_file() else (fp32_model if fp32_model.is_file() else None)
                if model_file and voices.is_file():
                    return model_file, voices

        return None, None

    def is_available(self) -> bool:
        try:
            import kokoro_onnx  # noqa: F401
            import soundfile  # noqa: F401
            model, voices = self._find_model_paths()
            return model is not None and voices is not None
        except ImportError:
            return False

    def _get_kokoro(self, config: Mapping[str, Any] | None = None):
        if self._kokoro_instance is not None:
            return self._kokoro_instance

        model_file, voices_file = self._find_model_paths(config)
        if not model_file or not voices_file:
            return None

        from kokoro_onnx import Kokoro
        self._kokoro_instance = Kokoro(str(model_file), str(voices_file))
        self._model_path = model_file
        self._voices_path = voices_file

        # Precompute the authentic North Indian English & Hindi blended styles via Norm-Preserving SLERP
        try:
            self._presets = {
                # 6 Research-Tested North Indian Personas
                "ni_delhi_corp_f": blend_norm_preserving(self._kokoro_instance, {"hf_alpha": 0.65, "bf_emma": 0.35}),
                "ni_kahani_f":     blend_norm_preserving(self._kokoro_instance, {"hf_beta": 0.60, "af_bella": 0.25, "bf_isabella": 0.15}),
                "ni_air_anchor_m": blend_norm_preserving(self._kokoro_instance, {"hm_omega": 0.70, "bm_george": 0.30}),
                "ni_ncr_tech_m":   blend_norm_preserving(self._kokoro_instance, {"hm_psi": 0.55, "bm_lewis": 0.30, "am_michael": 0.15}),
                "ni_fm_rj_f":      blend_norm_preserving(self._kokoro_instance, {"hf_alpha": 0.50, "af_heart": 0.35, "bf_alice": 0.15}),
                "ni_docu_deep_m":  blend_norm_preserving(self._kokoro_instance, {"hm_omega": 0.65, "am_adam": 0.35}),
                # Native stock voices
                "hf_alpha": self._kokoro_instance.get_voice_style("hf_alpha"),
                "hf_beta":  self._kokoro_instance.get_voice_style("hf_beta"),
                "hm_omega": self._kokoro_instance.get_voice_style("hm_omega"),
                "hm_psi":   self._kokoro_instance.get_voice_style("hm_psi"),
            }
            # Aliases for convenience
            self._presets["en_in_female"] = self._presets["ni_delhi_corp_f"]
            self._presets["en_in_male"] = self._presets["ni_air_anchor_m"]
            self._blended_en_in_style = self._presets["ni_delhi_corp_f"]
        except Exception:
            self._presets = {}
            self._blended_en_in_style = "af_heart"

        return self._kokoro_instance

    def synthesize_and_play(
        self,
        text: str,
        lang: str = "auto",
        blocking: bool = False,
        speed: float = 1.0,
        config: Mapping[str, Any] | None = None,
    ) -> bool:
        if not text or not text.strip():
            return False

        try:
            kokoro = self._get_kokoro(config)
            if kokoro is None:
                return False

            import soundfile as sf

            cfg = config or {}
            
            # Determine if the text is predominantly Hindi / Devanagari
            dev_count = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
            lat_count = sum(1 for ch in text if ("a" <= ch.lower() <= "z"))
            is_hindi = (lang == "hi") or (dev_count > 0 and dev_count >= lat_count)

            # Resolve voice selection:
            # 1. Direct explicit voice in config ("voice", "kokoro_voice", "tts_voice")
            # 2. Language-specific voice in config ("kokoro_voice_hi" or "kokoro_voice_en")
            # 3. Default preset for language
            explicit_voice = (
                cfg.get("voice")
                or cfg.get("kokoro_voice")
                or cfg.get("tts_voice")
            )
            if explicit_voice:
                voice_req = explicit_voice
            elif is_hindi:
                voice_req = cfg.get("kokoro_voice_hi", "hf_alpha")
            else:
                voice_req = cfg.get("kokoro_voice_en", "en_in_female")

            if voice_req in self._presets:
                voice = self._presets[voice_req]
            elif voice_req in kokoro.get_voices():
                voice = voice_req
            else:
                voice = self._blended_en_in_style if self._blended_en_in_style is not None else "hf_alpha"

            if is_hindi:
                kokoro_lang = "hi"
                samples, sample_rate = kokoro.create(
                    text,
                    voice=voice,
                    speed=speed,
                    lang=kokoro_lang,
                )
            else:
                kokoro_lang = cfg.get("kokoro_phoneme_lang", "en-gb")
                # Fix Indian proper names in phoneme space for authentic North Indian pronunciation
                phonemes = kokoro.tokenizer.phonemize(text, lang=kokoro_lang)
                phonemes = phonemes.replace("mˈanɒdʒ", "mənˈoːdʒ").replace("mˈænɑːdʒ", "mənˈoːdʒ")
                phonemes = phonemes.replace("ˈʊtɐɹɐkˌʌnd", "ˈʊtɐɹəkˌʌnd")
                phonemes = phonemes.replace("tʃˈeɪmbə", "tʃˈəmbɑː")
                phonemes = phonemes.replace("dˌeəɹɐdˈuːn", "dˈeːɦɹɑːdˌuːn")

                samples, sample_rate = kokoro.create(
                    phonemes,
                    voice=voice,
                    speed=speed,
                    lang=kokoro_lang,
                    is_phonemes=True,
                )

            if samples is None or len(samples) == 0:
                return False

            paplay = shutil.which("paplay") or shutil.which("aplay")
            if not paplay:
                return False

            tmp_path = tempfile.mktemp(suffix=".wav")
            sf.write(tmp_path, samples, sample_rate)

            play = subprocess.Popen([paplay, tmp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            from pwd_helper.tts.dispatcher import get_dispatcher
            get_dispatcher().set_active_proc(play)

            if blocking:
                play.wait()

            def _cleanup():
                try:
                    play.wait()
                finally:
                    if os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass

            threading.Thread(target=_cleanup, daemon=True).start()
            return True
        except Exception:
            return False
