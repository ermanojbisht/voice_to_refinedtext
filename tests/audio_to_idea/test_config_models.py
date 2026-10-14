import json
from pathlib import Path

import pytest
from audio_to_idea.config import DEFAULTS, load_settings, save_settings, update_settings
from audio_to_idea.models import discover, inspect_model, resolve_model
from audio_to_idea.schemas import AudioToIdeaError


def model(folder):
    folder.mkdir(parents=True)
    for name in ['config.json', 'tokenizer.json', 'preprocessor_config.json']:
        (folder / name).write_text('{}')
    (folder / 'model.bin').write_bytes(b'fixture weights')
    return folder


def test_precedence_paths_extensions_and_roundtrip(tmp_path):
    config = tmp_path / 'settings.json'
    config.write_text(json.dumps({'version': 1, 'asr': {'cache_root': 'cache space', 'device': 'cpu'},
                                 'extra': {'hello': 3}}))
    settings = load_settings(config, {'asr.device': 'auto'}, {'AUDIO2IDEA_DEVICE': 'cuda'}, tmp_path / 'none')
    assert settings.data['asr']['device'] == 'auto'
    assert settings.data['asr']['cache_root'] == str(tmp_path / 'cache space')
    assert settings.sources['asr.device'] == 'command line'
    save_settings(config, settings.data)
    assert json.loads(config.read_text())['extra']['hello'] == 3


@pytest.mark.parametrize('overrides', [{'asr.device': 'mps'}, {'audio.chunk_seconds': 0},
    {'audio.overlap_seconds': 60}, {'asr.cpu_threads': -1}, {'output.formats': ['docx']},
    {'asr.offline': 'true'}, {'synthesis.host': 'https://remote.example'}, {'asr.allow_downloads': True}])
def test_invalid_explicit_settings(tmp_path, overrides):
    with pytest.raises(AudioToIdeaError):
        load_settings(overrides=overrides, environ={}, legacy_path=tmp_path / 'none')


def test_alias_conflict_and_missing_explicit_file(tmp_path):
    with pytest.raises(AudioToIdeaError, match='conflict'):
        load_settings(environ={'ASR_MODEL_PATH': '/a', 'AUDIO2IDEA_MODEL_PATH': '/b'})
    with pytest.raises(AudioToIdeaError, match='does not exist'):
        load_settings(tmp_path / 'absent')


def test_legacy_readonly_fallback(tmp_path):
    legacy = tmp_path / 'legacy.json'
    legacy.write_text(json.dumps({'WHISPER_MODEL': 'small', 'OLLAMA_HOST': 'http://localhost:1',
                                 'OLLAMA_MODELS': {'en': 'test'}, 'SILENCE_THRESHOLD': 999}))
    before = legacy.read_bytes()
    cfg = load_settings(legacy_path=legacy, environ={}).data
    assert cfg['asr']['model_id'] == 'Systran/faster-whisper-small'
    assert cfg['synthesis']['model'] == 'test'
    assert 'silence_threshold' not in cfg['audio']
    assert legacy.read_bytes() == before


def test_snapshot_selection_format_and_broken_links(tmp_path):
    repo = tmp_path / 'models--Systran--faster-whisper-large-v3'
    valid = model(repo / 'snapshots' / 'good')
    asr = {**DEFAULTS['asr'], 'cache_root': str(tmp_path)}
    with pytest.raises(AudioToIdeaError, match='Compatible revisions'):
        resolve_model(asr)
    (repo / 'refs').mkdir()
    (repo / 'refs/main').write_text('good')
    assert resolve_model(asr)['path'] == str(valid)
    (valid / 'tokenizer.json').unlink()
    (valid / 'tokenizer.json').symlink_to(tmp_path / 'missing')
    with pytest.raises(AudioToIdeaError, match='Broken cache links'):
        resolve_model(asr)
    raw = tmp_path / 'raw'
    raw.mkdir()
    (raw / 'model.safetensors').write_bytes(b'weights')
    assert 'Transformers' in inspect_model(raw)['problems'][0]
    assert len(discover(asr)) == 1


def test_no_network_or_weight_load_during_offline_resolution(tmp_path, monkeypatch):
    import socket
    monkeypatch.setattr(socket, 'socket', lambda *a, **kw: pytest.fail('network attempt'))
    with pytest.raises(AudioToIdeaError, match='No download attempted'):
        resolve_model({**DEFAULTS['asr'], 'cache_root': str(tmp_path)})


def test_high_priority_selection_overrides_saved_folder(tmp_path):
    file = tmp_path / 'settings.json'
    file.write_text(json.dumps({'asr': {'model_path': '/old/pc/model'}}))
    cfg = load_settings(file, {'asr.model_id': 'tiny'}, environ={}).data
    assert cfg['asr']['model_path'] is None and cfg['asr']['model_id'] == 'Systran/faster-whisper-tiny'
    cfg = load_settings(file, {'asr.model_id': 'tiny', 'asr.model_path': str(tmp_path)}, environ={}).data
    assert cfg['asr']['model_path'] == str(tmp_path)


def test_invalid_legacy_file_does_not_block_independent_settings(tmp_path):
    legacy = tmp_path / 'old.json'
    legacy.write_text('{broken')
    cfg = load_settings(environ={}, legacy_path=legacy)
    assert cfg.data['asr']['model_id'] == DEFAULTS['asr']['model_id']
    assert 'ignored' in cfg.sources['legacy']


def test_sparse_theme_update_preserves_settings_and_transient_overrides(tmp_path):
    path = tmp_path / 'settings.json'
    original = {'asr': {'cache_root': './portable cache', 'device': 'cpu'}, 'extension': {'keep': 4}}
    path.write_text(json.dumps(original))
    cfg = load_settings(path, {'asr.device': 'cuda'}, environ={}, legacy_path=tmp_path / 'none')
    assert cfg.data['ui']['appearance'] == 'system'
    update_settings(path, {'ui.appearance': 'light'})
    assert json.loads(path.read_text()) == {**original, 'ui': {'appearance': 'light'}}
    assert load_settings(path, environ={}, legacy_path=tmp_path / 'none').data['asr']['device'] == 'cpu'
    before = path.read_bytes()
    with pytest.raises(AudioToIdeaError, match='Appearance'):
        update_settings(path, {'ui.appearance': 'sepia'})
    assert path.read_bytes() == before
