"""Capture legacy contracts before adding shared inference coordination.

All persistent files live in pytest temporary directories. External effects are
faked so a regression run cannot type text, narrate, or alter the user's vault.
"""
import ast
import importlib.util
import json
import types
from pathlib import Path
from unittest.mock import Mock

import pytest
import utils
import review_engine as review

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def voice(monkeypatch, tmp_path):
    keyboard = types.ModuleType('pynput.keyboard')
    keyboard.Controller = Mock()
    package = types.ModuleType('pynput')
    package.keyboard = keyboard
    monkeypatch.setitem(__import__('sys').modules, 'pynput', package)
    monkeypatch.setitem(__import__('sys').modules, 'pynput.keyboard', keyboard)
    spec = importlib.util.spec_from_file_location('isolated_legacy_engine', ROOT / 'engine.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    instance = module.VoiceEngine(str(tmp_path))
    instance.log = Mock()
    return instance


def segment(text, probability=0.0):
    return types.SimpleNamespace(text=text, no_speech_prob=probability)


@pytest.mark.parametrize('detected,forced', [('en', None), ('ur', 'hi'), ('hi', 'hi'), ('fr', 'en')])
def test_language_and_string_contract(voice, detected, forced):
    model = Mock()
    model.transcribe.side_effect = lambda *args, **kw: (
        iter([segment('Hello'), segment('123'), segment('!!!'), segment('noise', .9), segment(' दुनिया ')]),
        types.SimpleNamespace(language=detected))
    voice._whisper_model = model
    assert voice.transcribe('unused.wav') == 'Hello दुनिया'
    assert model.transcribe.call_count == (2 if forced else 1)
    if forced:
        assert model.transcribe.call_args.kwargs['language'] == forced


def test_refine_and_translate_model_selection(voice, monkeypatch):
    voice.config['OLLAMA_MODELS'] = {'en': 'english'}
    voice.config['OLLAMA_TRANSLATE_MODELS'] = {'to_en': 'translator'}
    monkeypatch.setattr(utils, 'detect_lang', lambda _: 'en')
    monkeypatch.setattr(utils, 'get_prompt_and_stops', lambda *a, **kw: ('prompt', []))
    call = Mock(return_value={'response': ' polished '})
    monkeypatch.setattr(utils, 'call_ollama', call)
    assert voice.refine('hello') == 'polished'
    assert call.call_args.args[1] == 'english'
    monkeypatch.setattr(utils, 'detect_lang', lambda _: 'hi')
    assert voice.refine('नमस्ते', mode='translate') == 'polished'
    assert call.call_args.args[1] == 'translator'
    assert voice.refine(' ') == 'No speech detected.'


def test_config_preserves_extensions_and_nested_defaults(tmp_path):
    data = {'custom_extension': {'value': 9}, 'FEATURES': {'clipboard_output': False}}
    (tmp_path / 'config.json').write_text(json.dumps(data))
    cfg = utils.load_config(str(tmp_path))
    assert cfg['custom_extension'] == {'value': 9}
    assert cfg['FEATURES']['clipboard_output'] is False
    assert cfg['FEATURES']['evening_review'] is True
    assert json.loads((tmp_path / 'config.json').read_text()) == data


@pytest.fixture
def isolated_review(monkeypatch, tmp_path):
    for attr, name in [('STATE_PATH', 'state.json'), ('_PROCESSING_LOCK_PATH', 'processing.lock'),
                       ('_NARRATION_PID_FILE', 'narration.pid'), ('_NARRATION_TEXT_FILE', 'last.txt')]:
        monkeypatch.setattr(review, attr, str(tmp_path / name))
    for name in ['send_step_notification', 'send_notification', 'narrate', '_append_focus_word', '_log_review']:
        monkeypatch.setattr(review, name, Mock())
    cfg = {'review_expiry_hours': 24, 'focus_word_trend': False,
           'vault_paths': {'daily_notes': str(tmp_path / 'daily'), 'wellness_notes': str(tmp_path / 'wellness')},
           'review_steps': [{'step_id': 1, 'section_name': 'Achievements'},
                            {'step_id': 2, 'section_name': 'Movement', 'skip_default': 'only office'},
                            {'step_id': 3, 'section_name': 'Wellness', 'isolate_file': True}]}
    state = {'date': '2026-10-12', 'active': True, 'current_step_index': 0, 'accumulated_raw': [],
             'started_at': __import__('datetime').datetime.now().isoformat()}
    review._save_state(state)
    return cfg, state, tmp_path


def test_review_accumulate_and_structure(isolated_review):
    cfg, state, folder = isolated_review
    review.accumulate_clip(state, 'first')
    review.accumulate_clip(state, 'second')
    assert review.load_state()['awaiting_more'] is True
    assert review.structure_and_advance(str(folder), Mock(), cfg) == (True, None, True)
    after = review.load_state()
    assert after['current_step_index'] == 1
    assert after['interview_raw']['1'] == 'first\nsecond'
    assert not after.get('processing')


def test_review_duplicate_advance_guard(isolated_review):
    cfg, state, folder = isolated_review
    held = review._acquire_processing_lock()
    try:
        assert review.structure_and_advance(str(folder), Mock(), cfg) == (False, None, True)
        assert review.load_state()['current_step_index'] == 0
    finally:
        review._release_processing_lock(held)


def test_note_date_redo_skip_and_isolated_output(isolated_review):
    cfg, state, folder = isolated_review
    review.write_step_to_note(str(folder), cfg, cfg['review_steps'][0], 'Completed inspection', state)
    note = Path(state['last_written']['file'])
    assert '2026-10-12' in note.name
    assert 'Completed inspection' in note.read_text()
    review.redo_step(str(folder), state, cfg)
    assert 'Completed inspection' not in note.read_text()
    state['current_step_index'] = 1
    review.skip_step(str(folder), state, cfg)
    assert 'only office' in note.read_text()
    review.write_step_to_note(str(folder), cfg, cfg['review_steps'][2], 'Slept well', state)
    assert 'wellness' in state['last_written']['file']
    assert 'Slept well' not in note.read_text()


def load_tray_method(name):
    # Extract only the production method: importing pystray would bind a display.
    tree = ast.parse((ROOT / 'tray_app.py').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'VoiceAssistantTray')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    scope = {'subprocess': types.SimpleNamespace(run=Mock()), 'os': __import__('os'), '_tlog': Mock()}
    exec(compile(ast.Module(body=[method], type_ignores=[]), 'tray_app.py', 'exec'), scope)
    return scope[name], scope


@pytest.mark.parametrize('clipboard,typing', [(False, False), (True, False), (False, True), (True, True)])
def test_tray_output_feature_flags(clipboard, typing):
    run, scope = load_tray_method('_run_normal_mode')
    engine = Mock(config={'FEATURES': {'clipboard_output': clipboard, 'direct_typing': typing}})
    engine.refine.return_value = 'polished'
    app = types.SimpleNamespace(engine=engine, script_dir='/unused', _notify=Mock())
    run(app, 'raw')
    calls = scope['subprocess'].run.call_args_list
    assert any('xclip' in str(c.args[0]) for c in calls) == clipboard
    assert engine.type_text.called == typing
