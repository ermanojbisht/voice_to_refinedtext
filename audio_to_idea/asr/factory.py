"""Factory for constructing and resolving ASR providers with resilient fallbacks.

Handles:
- Configuration parsing for VoiceEngine (`engine.py`)
- Settings parsing for AudioToIdea (`audio_to_idea`)
- Wake-word listener initialization (`voice_control.py`)
- Automatic fallback chain: TranscribeCpp -> HandyCli -> FasterWhisper
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, Optional

from .base import BaseASRProvider
from .faster_whisper import FasterWhisperProvider
from .handy_cli import HandyCliProvider
from .transcribe_cpp import TranscribeCppProvider

DEFAULT_NEMOTRON_PATH = "/media/manoj/F1/models-handy/nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf"


class ASRFactory:
    """Creates BaseASRProvider instances based on configuration dictionaries."""

    @staticmethod
    def from_engine_config(config: Dict[str, Any]) -> BaseASRProvider:
        """Build provider for VoiceEngine in engine.py."""
        # 1. Resolve from modern ASR_PRESETS if present
        active_preset_key = config.get("ACTIVE_ASR_PRESET")
        presets = config.get("ASR_PRESETS", {})
        if active_preset_key and active_preset_key in presets:
            preset = presets[active_preset_key]
            backend = preset.get("backend", "faster_whisper").lower()
            model_path = preset.get("model") or config.get("WHISPER_FALLBACK_MODEL", "large-v3-turbo")
            device = preset.get("device", "auto")

            if backend == "transcribe_cpp":
                provider = TranscribeCppProvider(
                    model_path=model_path,
                    family="nemotron" if "nemotron" in str(model_path).lower() else "whisper",
                    device=device,
                )
                if provider.is_available():
                    return provider
                fallback = config.get("WHISPER_FALLBACK_MODEL", "large-v3-turbo")
                return FasterWhisperProvider(model_path_or_id=fallback, device=device)

            if backend == "faster_whisper":
                return FasterWhisperProvider(model_path_or_id=model_path, device=device)

            if backend == "handy_cli":
                handy_prov = HandyCliProvider(model_id=preset.get("model_id"))
                if handy_prov.is_available():
                    return handy_prov
                return FasterWhisperProvider(model_path_or_id=config.get("WHISPER_FALLBACK_MODEL", "large-v3-turbo"))

        # 2. Legacy fallback to MODEL_PROFILES / ASR_ENGINE
        engine_type = config.get("ASR_ENGINE", "").lower()
        active_profile_key = config.get("ACTIVE_MODEL_PROFILE", "nemotron_fast")
        profiles = config.get("MODEL_PROFILES", {})

        profile = profiles.get(active_profile_key, {})

        if engine_type == "transcribe_cpp" or profile.get("backend") == "transcribe_cpp":
            model_path = profile.get("path") or DEFAULT_NEMOTRON_PATH
            provider = TranscribeCppProvider(
                model_path=model_path,
                family=profile.get("family", "nemotron"),
                device=profile.get("device", "auto"),
            )
            if provider.is_available():
                return provider

            # Fallback 1: Handy CLI
            handy_prov = HandyCliProvider()
            if handy_prov.is_available():
                return handy_prov

            # Fallback 2: Faster Whisper
            return FasterWhisperProvider(model_path_or_id=config.get("WHISPER_MODEL", "large-v3-turbo"))

        if engine_type == "handy_cli" or profile.get("backend") == "handy_cli":
            handy_prov = HandyCliProvider(model_id=profile.get("model_id"))
            if handy_prov.is_available():
                return handy_prov
            return FasterWhisperProvider(model_path_or_id=config.get("WHISPER_MODEL", "large-v3-turbo"))

        # Faster-Whisper provider path
        whisper_model = profile.get("path") or config.get("WHISPER_MODEL", "large-v3-turbo")
        device = profile.get("device", "auto")
        return FasterWhisperProvider(model_path_or_id=whisper_model, device=device)

    @staticmethod
    def from_settings(settings: Dict[str, Any]) -> BaseASRProvider:
        """Build provider for AudioToIdea batch processor from settings dictionary."""
        asr_cfg = settings.get("asr", {})
        backend = asr_cfg.get("backend", "faster-whisper").lower().replace("-", "_")
        active_profile_key = asr_cfg.get("active_profile")
        profiles = asr_cfg.get("model_profiles", {})

        profile = profiles.get(active_profile_key, {}) if active_profile_key else {}

        if backend == "transcribe_cpp" or profile.get("backend") == "transcribe_cpp":
            model_path = profile.get("path") or asr_cfg.get("model_path") or asr_cfg.get("model_id") or DEFAULT_NEMOTRON_PATH
            family = profile.get("family")
            if not family:
                m_str = str(model_path).lower()
                family = "whisper" if ("apex" in m_str or "whisper" in m_str) else "nemotron"
            provider = TranscribeCppProvider(
                model_path=model_path,
                family=family,
                device=asr_cfg.get("device", "auto"),
            )
            if provider.is_available():
                return provider

        if backend == "handy_cli" or profile.get("backend") == "handy_cli":
            provider = HandyCliProvider(model_id=profile.get("model_id"))
            if provider.is_available():
                return provider

        # Default to FasterWhisperProvider
        model_path_or_id = (
            profile.get("path")
            or asr_cfg.get("model_path")
            or asr_cfg.get("model_id")
            or "large-v3-turbo"
        )
        return FasterWhisperProvider(
            model_path_or_id=str(model_path_or_id),
            device=asr_cfg.get("device", "auto"),
            compute_type=asr_cfg.get("compute_type", "auto"),
            cpu_threads=asr_cfg.get("cpu_threads", 4),
            word_timestamps=asr_cfg.get("word_timestamps", True),
            offline=asr_cfg.get("offline", True),
        )

    @staticmethod
    def from_wake_word_config() -> BaseASRProvider:
        """Build fast, lightweight provider for voice wake words in Evening Review."""
        nemotron = TranscribeCppProvider(model_path=DEFAULT_NEMOTRON_PATH)
        if nemotron.is_available():
            return nemotron

        # Fallback to tiny CPU whisper
        return FasterWhisperProvider(
            model_path_or_id="tiny",
            device="cpu",
            compute_type="int8",
            word_timestamps=False,
        )
