"""Explicit opt-in inference tests against existing caches; no downloads."""
from copy import deepcopy
import os
from pathlib import Path

import pytest
from audio_to_idea.config import DEFAULTS
from audio_to_idea.jobs import JobService
from audio_to_idea.storage import read_json

pytestmark = [pytest.mark.local_model, pytest.mark.skipif(not os.environ.get('AUDIO2IDEA_TEST_CACHE'),
              reason='Set AUDIO2IDEA_TEST_CACHE to a complete local cache to run inference checks.')]


@pytest.fixture(scope='module')
def recordings(tmp_path_factory):
    import importlib.util
    script = Path(__file__).parents[1] / 'make_audio_fixtures.py'
    spec = importlib.util.spec_from_file_location('fixtures_generator', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    folder = tmp_path_factory.mktemp('annotated_audio')
    annotations = module.generate(folder)
    return folder, annotations


@pytest.mark.parametrize('model_id', ['Systran/faster-whisper-large-v3', 'mobiuslabsgmbh/faster-whisper-large-v3-turbo'])
def test_gpu_pause_boundary_tail(model_id, recordings, tmp_path):
    folder, annotations = recordings
    cfg = deepcopy(DEFAULTS)
    cfg['asr'].update(cache_root=os.environ['AUDIO2IDEA_TEST_CACHE'], model_id=model_id, device='cuda')
    cfg['audio'].update(chunk_seconds=12.0, overlap_seconds=1.5)
    result = JobService(cfg).run(folder / 'long_pause.wav', tmp_path, summary=False)
    assert result['status'] == 'complete', result
    transcript = read_json(result['transcript_path'])
    text = ' '.join(s['text'] for s in transcript['segments']).casefold()
    for word in annotations['long_pause']['critical_words']:
        assert word in text, text
    assert any(s['start'] >= annotations['long_pause']['tail_start'] - 1 for s in transcript['segments'])
    assert transcript['chunks'][-1]['end'] == transcript['duration']
    assert any('123' in s['text'] or 'hundred' in s['text'].casefold() for s in transcript['segments']), text


def test_cpu_tiny_and_hindi(recordings, tmp_path):
    folder, _ = recordings
    cfg = deepcopy(DEFAULTS)
    cfg['asr'].update(cache_root=os.environ['AUDIO2IDEA_TEST_CACHE'], model_id='Systran/faster-whisper-tiny', device='cpu')
    first = JobService(cfg).run(folder / 'first.wav', tmp_path / 'cpu', summary=False)
    assert first['status'] == 'complete', first
    assert 'bridge' in ' '.join(s['text'] for s in read_json(first['transcript_path'])['segments']).casefold()
    cfg['asr'].update(model_id='Systran/faster-whisper-large-v3', device='cuda', language='hi')
    from audio_to_idea.storage import write_json
    profile = tmp_path / 'hindi_context.json'
    write_json(profile, {'glossary': ['सड़क', 'निरीक्षण', 'पुल', 'मरम्मत', 'बैठक']})
    hindi = JobService(cfg).run(folder / 'hindi.wav', tmp_path / 'hindi', summary=False, profile=profile)
    assert hindi['status'] == 'complete', hindi
    text = ' '.join(s['text'] for s in read_json(hindi['transcript_path'])['segments'])
    # Nukta representation/spelling varies in ASR. Compare the same critical
    # lexical terms without that diacritic, while retaining untouched output.
    import unicodedata
    comparable = unicodedata.normalize('NFD', text).replace('\u093c', '')
    assert 'सडक' in comparable and 'पुल' in comparable and 'बैठक' in comparable, text


def test_actual_ollama_synthesis(tmp_path):
    from audio_to_idea.llm import OllamaClient
    from audio_to_idea.synthesis import extract
    cfg = deepcopy(DEFAULTS)
    cfg['synthesis']['model'] = os.environ.get('AUDIO2IDEA_TEST_LLM', 'qwen2.5:3b')
    transcript = {'revision': 'fixture-v1', 'segments': [{'id': 'S00001', 'text': 'The bridge inspection is delayed.'},
                  {'id': 'S00002', 'text': 'We should schedule a site visit on Friday.'}]}
    ideas = extract(transcript, {'background': 'Road maintenance review', 'title': 'fixture'}, cfg, OllamaClient(cfg))
    assert ideas['sections']['bottlenecks'], ideas
    assert ideas['sections']['proposals'], ideas
    assert ideas['sections']['implications'] == [], ideas
    assert all(item['evidence'] for items in ideas['sections'].values() for item in items)


def test_actual_ollama_casual_recording_with_project_background():
    """Reproduce the user's false executive report using the actual local model."""
    from audio_to_idea.llm import OllamaClient
    from audio_to_idea.profiles import load_profile
    from audio_to_idea.synthesis import extract, render_ideas
    cfg = deepcopy(DEFAULTS)
    cfg['synthesis']['model'] = os.environ.get('AUDIO2IDEA_TEST_LLM', 'qwen2.5:3b')
    transcript = {'revision': 'casual-fixture', 'source_name': 'input.wav', 'duration': 8.704,
                  'segments': [{'id': 'S00001', 'start': 1.36,
                                'text': 'I think you are fine. Copy my words and tell me.'}]}
    profile = load_profile(Path(__file__).parents[2] / 'audio_to_idea/example_profiles/project_review.json')
    client = OllamaClient(cfg)
    try:
        ideas = extract(transcript, profile, cfg, client)
    finally:
        client.close()
    assert ideas['sections'] == {'bottlenecks': [], 'proposals': [], 'implications': []}, ideas
    assert 'No actionable ideas identified' in render_ideas(ideas, transcript)


@pytest.mark.parametrize('mode', ['clean_paragraph', 'concise_summary'])
@pytest.mark.parametrize('text,terms', [
    ('Um, the inspection is on Friday. The budget is 123 lakh. The payment is not approved.', ['Friday', '123', 'not']),
    ('उम, निरीक्षण शुक्रवार को है। बजट 123 लाख है। भुगतान मंजूर नहीं है।', ['शुक्रवार', '123', 'नहीं']),
    ('RoW inspection शुक्रवार को है। Budget 123 lakh है। Payment approved नहीं है।', ['RoW', 'शुक्रवार', '123', 'नहीं']),
])
def test_actual_ollama_rewrite_languages(mode, text, terms):
    from audio_to_idea.llm import OllamaClient
    from audio_to_idea.rewriting import rewrite
    cfg = deepcopy(DEFAULTS)
    cfg['synthesis'].update(mode=mode, model=os.environ.get('AUDIO2IDEA_TEST_LLM', 'qwen2.5:3b'))
    client = OllamaClient(cfg)
    try:
        result = rewrite({'revision': 'language-fixture', 'segments': [{'id': 'S00001', 'text': text}]},
                         {'background': ''}, cfg, client)
    finally:
        client.close()
    for term in terms:
        assert term.casefold() in result['text'].casefold(), result
    assert 'S00001' not in result['text'] and 'EXECUTIVE' not in result['text']
