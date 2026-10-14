"""Modes, prompt edits and caching must not change source transcription."""
from copy import deepcopy
import json
from pathlib import Path
import threading

import pytest
from audio_to_idea.config import DEFAULTS, load_settings
from audio_to_idea.jobs import JobService
from audio_to_idea.rewriting import rewrite, validate_text
from audio_to_idea.schemas import AudioToIdeaError, Cancelled
from audio_to_idea.storage import read_json
from audio_to_idea.templates import load_template, validate_template
from test_audio_exports import wav
from test_config_models import model
from test_jobs_synthesis import FakeASR, FakeLLM


def test_mode_defaults_precedence_and_portable_paths(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'synthesis': {'prompt_directory': 'my prompts'}}))
    cfg = load_settings(path, environ={}, legacy_path=tmp_path / 'none')
    assert cfg.data['synthesis']['mode'] == 'clean_paragraph'
    assert cfg.data['synthesis']['prompt_directory'] == str(tmp_path / 'my prompts')
    cfg = load_settings(path, {'synthesis.mode': 'ideas_actions'}, environ={'AUDIO2IDEA_MODE': 'concise_summary'})
    assert cfg.data['synthesis']['mode'] == 'ideas_actions'
    with pytest.raises(AudioToIdeaError, match='Processing mode'):
        load_settings(path, {'synthesis.mode': 'unknown'}, environ={})


@pytest.mark.parametrize('text', ['', 'No transcript here', '{transcript} {transcript}', '{transcript} {unknown}'])
def test_invalid_templates_rejected(text):
    with pytest.raises(AudioToIdeaError):
        validate_template(text)


def test_template_substitution_is_single_pass_and_preserves_json_braces(tmp_path):
    cfg = deepcopy(DEFAULTS)
    path = tmp_path / 'prompt.txt'
    path.write_text('Return {"text":"..."}. {context}\n{transcript}\n{output_language}')
    cfg['synthesis']['prompt_file'] = str(path)
    template = load_template(cfg)
    rendered = template.render('Speech containing {context}', 'Background {transcript}', 'source')
    assert 'Speech containing {context}' in rendered and 'Background {transcript}' in rendered
    assert '{"text":"..."}' in rendered
    path.unlink()
    with pytest.raises(AudioToIdeaError, match='Cannot read prompt'):
        load_template(cfg)


def test_mode_outputs_template_cache_and_batch_snapshot(tmp_path):
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    cfg['synthesis']['model'] = 'fake'
    directory = tmp_path / 'prompts'
    directory.mkdir()
    custom = directory / 'clean_paragraph.txt'
    custom.write_text('Clean clearly. {transcript}')
    cfg['synthesis']['prompt_directory'] = str(directory)
    source = wav(tmp_path / 'note.wav')
    FakeASR.calls = FakeLLM.calls = 0
    FakeLLM.fail = False
    service = JobService(cfg, FakeASR, FakeLLM)
    first = service.run(source)
    assert first['status'] == 'complete' and Path(first['processed_path']).name == 'note_clean.txt'
    original = Path(first['transcript_path']).read_bytes()
    assert service.run(source)['status'] == 'complete'
    assert (FakeASR.calls, FakeLLM.calls) == (1, 1)
    custom.write_text('Tailored clean text. {transcript}')
    # An active service keeps its prompt snapshot; a fresh run sees the edit.
    assert service.run(source)['status'] == 'complete' and FakeLLM.calls == 1
    changed = JobService(cfg, FakeASR, FakeLLM).run(source)
    assert changed['status'] == 'complete' and FakeASR.calls == 1 and FakeLLM.calls == 2
    assert changed['synthesis_path'] != first['synthesis_path']
    for mode, suffix in [('concise_summary', 'summary'), ('ideas_actions', 'idea')]:
        cfg['synthesis']['mode'] = mode
        result = JobService(cfg, FakeASR, FakeLLM).run(source)
        assert result['status'] == 'complete', result
        assert Path(result['processed_path']).name == f'note_{suffix}.txt'
        assert Path(result['transcript_path']).read_bytes() == original
    assert FakeASR.calls == 1
    assert (tmp_path / 'note_clean.txt').exists()
    assert read_json(tmp_path / 'note.meta.json')['synthesis_mode'] == 'ideas_actions'


def test_long_multilingual_input_budget_empty_and_cancellation():
    calls = []
    class Client:
        def generate(self, prompt, schema):
            assert len(prompt.encode()) < 8192
            calls.append(prompt)
            return {'text': 'निरीक्षण delayed है, budget 123 lakh है।'}
    transcript = {'revision': 'r', 'segments': [{'id': 'S00001', 'text': 'निरीक्षण delayed है। ' * 2500}]}
    result = rewrite(transcript, {'background': '', 'title': 'test'}, DEFAULTS, Client())
    assert len(calls) > 1 and '123' in result['text']
    calls.clear()
    assert rewrite({'revision': 'r', 'segments': []}, {'background': ''}, DEFAULTS, Client())['text'] == ''
    assert not calls
    cancel = threading.Event(); cancel.set()
    with pytest.raises(Cancelled):
        rewrite(transcript, {'background': ''}, DEFAULTS, Client(), cancel)


def test_invalid_prompt_does_not_break_transcript_only(tmp_path):
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    cfg['synthesis']['prompt_file'] = str(tmp_path / 'missing.txt')
    source = wav(tmp_path / 'note.wav')
    assert JobService(cfg, FakeASR, FakeLLM).run(source, summary=False)['status'] == 'complete'
    assert JobService(cfg, FakeASR, FakeLLM).run(source)['status'] == 'failed'


def test_invalid_rewrite_gets_one_correction_then_preserves_transcript():
    class Client:
        calls = 0
        def generate(self, prompt, schema):
            self.calls += 1
            return {'text': ''}
    client = Client()
    with pytest.raises(AudioToIdeaError, match='Transcript is preserved'):
        rewrite({'revision': 'r', 'segments': [{'id': 'S00001', 'text': 'Hello'}]}, {'background': ''}, DEFAULTS, client)
    assert client.calls == 2


def test_cli_mode_and_prompt_flags_are_transient(tmp_path, monkeypatch, capsys):
    from audio_to_idea import cli
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    cfg['synthesis']['model'] = 'fake'
    path = tmp_path / 'settings.json'; path.write_text(json.dumps(cfg))
    prompt = tmp_path / 'custom.txt'; prompt.write_text('Summarize: {transcript}')
    source = wav(tmp_path / 'note.wav')
    before = path.read_bytes()
    FakeLLM.fail = False
    monkeypatch.setattr(cli, 'JobService', lambda c: JobService(c, FakeASR, FakeLLM))
    assert cli.main(['process', '--config', str(path), '-i', str(source), '--mode', 'concise_summary',
                     '--prompt-file', str(prompt), '--output-language', 'English', '--json']) == 0
    result = json.loads(capsys.readouterr().out)['results'][0]
    assert result['synthesis_mode'] == 'concise_summary' and path.read_bytes() == before


def test_rewrite_rejects_figure_language_and_negation_changes_but_allows_translation():
    source = 'RoW inspection शुक्रवार को है। Budget 123 lakh है। Payment approved नहीं है।'
    for wrong in ['RoW inspection शुक्रवार को है। Budget 12 lakh है। Payment approved नहीं है।',
                  'RoW inspection is on Friday. Budget 123 lakh. Payment is not approved.',
                  'RoW inspection शुक्रवार को है। Budget 123 lakh है। Payment approved है।']:
        with pytest.raises(AudioToIdeaError):
            validate_text(wrong, source, 'source')
    validate_text('The inspection is on Friday. Budget 123 lakh. Payment is not approved.',
                  'निरीक्षण शुक्रवार को है। बजट 123 लाख है। भुगतान मंजूर नहीं है।', 'English')


def test_speech_request_filter_keeps_adjacent_substantive_facts():
    from audio_to_idea.synthesis import _speech_only_item
    assert _speech_only_item('I think you are fine. Copy my words and tell me.')
    assert _speech_only_item('Please transcribe my recording.')
    assert not _speech_only_item('The inspection is delayed. Copy my words and tell me.')
    assert not _speech_only_item('Copy the inspection report and submit it on Friday.')
