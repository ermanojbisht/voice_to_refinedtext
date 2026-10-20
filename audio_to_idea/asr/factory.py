"""Factory for constructing and resolving ASR providers with resilient fallbacks.

Handles:
- Multi-environment model path resolution (portable across home PC, office desktop, laptop)
- Configuration parsing for VoiceEngine (`engine.py`)
- Settings parsing for AudioToIdea (`audio_to_idea`)
- Wake-word listener initialization (`voice_control.py`)
- Automatic fallback chain: TranscribeCpp -> HandyCli -> FasterWhisper
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from .base import BaseASRProvider
from .faster_whisper import FasterWhisperProvider
from .handy_cli import HandyCliProvider
from .transcribe_cpp import TranscribeCppProvider

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resolve_model_path(
    model_path_or_name: Optional[str],
    models_dir: Optional[str] = None,
    default_filename: Optional[str] = None,
) -> str:
    """Resolves an ASR model file path with multi-environment fallback discovery.

    Supports:
    - User home expansion (~/models/...)
    - Configured MODELS_DIR directory
    - Environment variables: MODELS_DIR, VOICE_MODELS_DIR, HANDY_MODELS_DIR
    - Automatic search in standard fallbacks:
        1. Configured MODELS_DIR
        2. Environment variables ($MODELS_DIR, $VOICE_MODELS_DIR, $HANDY_MODELS_DIR)
        3. Project-local directory <project_root>/models/
        4. User local data dir ~/.local/share/voice_to_refinedtext/models/
        5. User cache dir ~/.cache/voice_to_refinedtext/models/
        6. Historical development path /media/manoj/F1/models-handy/
    """
    target = model_path_or_name or default_filename or "nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf"
    expanded = os.path.expanduser(str(target))

    # 1. Direct path exists
    if os.path.exists(expanded):
        return os.path.abspath(expanded)

    # 2. Relative to project root
    rel_project = os.path.join(PROJECT_ROOT, expanded)
    if os.path.exists(rel_project):
        return os.path.abspath(rel_project)

    # 3. Check candidate base directories
    filename = os.path.basename(expanded)
    candidate_dirs = []

    if models_dir:
        candidate_dirs.append(os.path.expanduser(str(models_dir)))

    for env_var in ("MODELS_DIR", "VOICE_MODELS_DIR", "HANDY_MODELS_DIR"):
        val = os.environ.get(env_var)
        if val:
            candidate_dirs.append(os.path.expanduser(val))

    candidate_dirs.extend([
        os.path.join(PROJECT_ROOT, "models"),
        os.path.expanduser("~/.local/share/voice_to_refinedtext/models"),
        os.path.expanduser("~/.cache/voice_to_refinedtext/models"),
        "/media/manoj/F1/models-handy",
    ])

    for cdir in candidate_dirs:
        candidate_file = os.path.join(cdir, filename)
        if os.path.isfile(candidate_file):
            return os.path.abspath(candidate_file)

    return expanded


DEFAULT_NEMOTRON_PATH = resolve_model_path("/media/manoj/F1/models-handy/nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf")


class ASRFactory:
    """Creates BaseASRProvider instances based on configuration dictionaries."""

    @staticmethod
    def from_engine_config(config: Dict[str, Any]) -> BaseASRProvider:
        """Build provider for VoiceEngine in engine.py."""
        models_dir = config.get("MODELS_DIR")

        # 1. Resolve from modern ASR_PRESETS if present
        active_preset_key = config.get("ACTIVE_ASR_PRESET")
        presets = config.get("ASR_PRESETS", {})
        if active_preset_key and active_preset_key in presets:
            preset = presets[active_preset_key]
            backend = preset.get("backend", "faster_whisper").lower().replace("-", "_")
            raw_model = preset.get("model") or config.get("WHISPER_FALLBACK_MODEL", "large-v3-turbo")
            device = preset.get("device", "auto")

            if backend == "transcribe_cpp":
                resolved_path = resolve_model_path(
                    raw_model,
                    models_dir=models_dir,
                    default_filename="nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf",
                )
                family = "nemotron" if "nemotron" in str(resolved_path).lower() else "whisper"
                provider = TranscribeCppProvider(
                    model_path=resolved_path,
                    family=family,
                    device=device,
                )
                if provider.is_available():
                    return provider
                fallback = config.get("WHISPER_FALLBACK_MODEL", "large-v3-turbo")
                return FasterWhisperProvider(model_path_or_id=fallback, device=device)

            if backend == "faster_whisper":
                return FasterWhisperProvider(model_path_or_id=raw_model, device=device)

            if backend == "handy_cli":
                handy_prov = HandyCliProvider(model_id=preset.get("model_id"))
                if handy_prov.is_available():
                    return handy_prov
                return FasterWhisperProvider(model_path_or_id=config.get("WHISPER_FALLBACK_MODEL", "large-v3-turbo"))

        # 2. Legacy fallback to MODEL_PROFILES / ASR_ENGINE
        engine_type = config.get("ASR_ENGINE", "").lower().replace("-", "_")
        active_profile_key = config.get("ACTIVE_MODEL_PROFILE", "nemotron_fast")
        profiles = config.get("MODEL_PROFILES", {})
        profile = profiles.get(active_profile_key, {})

        if engine_type == "transcribe_cpp" or profile.get("backend") == "transcribe_cpp":
            model_path = resolve_model_path(
                profile.get("path") or DEFAULT_NEMOTRON_PATH,
                models_dir=models_dir,
                default_filename="nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf",
            )
            provider = TranscribeCppProvider(
                model_path=model_path,
                family=profile.get("family", "nemotron"),
                device=profile.get("device", "auto"),
            )
            if provider.is_available():
                return provider
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
        models_dir = settings.get("MODELS_DIR") or asr_cfg.get("models_dir")

        profile = profiles.get(active_profile_key, {}) if active_profile_key else {}

        if backend == "transcribe_cpp" or profile.get("backend") == "transcribe_cpp":
            raw_path = profile.get("path") or asr_cfg.get("model_path") or asr_cfg.get("model_id") or DEFAULT_NEMOTRON_PATH
            resolved_path = resolve_model_path(
                raw_path,
                models_dir=models_dir,
                default_filename="nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf",
            )
            family = profile.get("family")
            if not family:
                m_str = str(resolved_path).lower()
                family = "whisper" if ("apex" in m_str or "whisper" in m_str) else "nemotron"
            provider = TranscribeCppProvider(
                model_path=resolved_path,
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
        nemotron_path = resolve_model_path(None, default_filename="nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf")
        nemotron = TranscribeCppProvider(model_path=nemotron_path)
        if nemotron.is_available():
            return nemotron

        # Fallback to tiny CPU whisper
        return FasterWhisperProvider(
            model_path_or_id="tiny",
            device="cpu",
            compute_type="int8",
            word_timestamps=False,
        )
