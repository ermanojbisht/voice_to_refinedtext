"""Unit tests for multi-environment model path portability and fallback resolution."""
import os
import tempfile
from pathlib import Path
import pytest

from audio_to_idea.asr.factory import resolve_model_path, ASRFactory
from audio_to_idea.models import cache_root


def test_resolve_model_path_direct_existing():
    """Existing absolute path must resolve directly."""
    with tempfile.NamedTemporaryFile(suffix=".gguf") as f:
        resolved = resolve_model_path(f.name)
        assert resolved == os.path.abspath(f.name)


def test_resolve_model_path_expanduser(monkeypatch, tmp_path):
    """Path starting with ~ should expand to home directory."""
    monkeypatch.setenv("HOME", str(tmp_path))
    model_file = tmp_path / "my_model.gguf"
    model_file.write_text("dummy")

    resolved = resolve_model_path("~/my_model.gguf")
    assert resolved == str(model_file.resolve())


def test_resolve_model_path_via_models_dir(tmp_path):
    """When configured path is from another PC, it should find the file in MODELS_DIR."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    target_file = models_dir / "custom_model.gguf"
    target_file.write_text("model bytes")

    foreign_path = "/media/other_pc/drive/custom_model.gguf"
    resolved = resolve_model_path(foreign_path, models_dir=str(models_dir))
    assert resolved == str(target_file.resolve())


def test_resolve_model_path_via_env_var(tmp_path, monkeypatch):
    """When configured path is absent, check environment variable MODELS_DIR."""
    models_dir = tmp_path / "env_models"
    models_dir.mkdir()
    target_file = models_dir / "apex_model.bin"
    target_file.write_text("apex bytes")

    monkeypatch.setenv("MODELS_DIR", str(models_dir))
    foreign_path = "/nonexistent/drive/apex_model.bin"
    resolved = resolve_model_path(foreign_path)
    assert resolved == str(target_file.resolve())


def test_cache_root_falls_back_to_hf_home_when_not_explicitly_configured(monkeypatch, tmp_path):
    """When cache_root is not explicitly configured, fall back to HF_HOME / hub."""
    fake_hf_home = tmp_path / "hf_home"
    monkeypatch.setenv("HF_HOME", str(fake_hf_home))

    asr_cfg = {"cache_root": None}
    resolved_root = cache_root(asr_cfg)

    assert str(fake_hf_home / "hub") in str(resolved_root)


def test_resolve_relative_model_filename_from_config_presets(tmp_path):
    """Relative filename in ASR_PRESETS resolves cleanly via MODELS_DIR."""
    models_dir = tmp_path / "custom_models"
    models_dir.mkdir()
    nemotron_file = models_dir / "nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf"
    nemotron_file.write_text("gguf dummy")

    cfg = {
        "MODELS_DIR": str(models_dir),
        "ACTIVE_ASR_PRESET": "instant_english",
        "ASR_PRESETS": {
            "instant_english": {
                "backend": "transcribe_cpp",
                "model": "nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf",
            }
        },
    }
    prov = ASRFactory.from_engine_config(cfg)
    assert prov.model_path == str(nemotron_file.resolve())
