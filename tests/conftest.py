"""Test isolation: never initialize the user's microphone, keyboard or models."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def isolated_module_settings(monkeypatch, tmp_path):
    from audio_to_idea import config
    monkeypatch.setattr(config, 'default_config_path', lambda: tmp_path / 'audio_to_idea_config.json')
    monkeypatch.setenv('AUDIO2IDEA_RESOURCE_DIR', str(tmp_path / 'resources'))

