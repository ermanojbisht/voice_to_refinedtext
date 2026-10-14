from copy import deepcopy
import json
from pathlib import Path
import threading

import pytest
from audio_to_idea.config import DEFAULTS
from audio_to_idea.jobs import JobService, save_transcript_edit
from audio_to_idea.storage import read_json
from audio_to_idea.synthesis import extract
from audio_to_idea.schemas import AudioToIdeaError
from audio_to_idea.watcher import Watcher
from test_config_models import model
from test_audio_exports import wav


class FakeASR:
    calls = 0
    def __init__(self, *args): pass
    def transcribe(self, path, chunk, glossary):
        FakeASR.calls += 1
        return {'index': chunk.index, 'start': chunk.start, 'end': chunk.end, 'language': 'hi',
                'segments': [{'start': chunk.start, 'end': chunk.end, 'text': 'Inspect 123 किलोमीटर', 'words': []}]}
    def close(self): pass


class FakeLLM:
    calls = 0
    fail = False
    def __init__(self, *args): pass
    def generate(self, prompt, schema):
        FakeLLM.calls += 1
        if FakeLLM.fail:
            raise AudioToIdeaError('Unavailable')
        # Respect the production contract: spoken items quote the actual input,
        # including edited revisions, rather than manufacturing a paraphrase.
        import re
        quote = re.search(r'\[S00001\] ([^\n]+)', prompt).group(1)
        if 'text' in schema['properties']:
            return {'text': quote}
        return {'bottlenecks': [{'text': quote, 'kind': 'spoken', 'evidence': ['S00001']}],
                'proposals': [], 'implications': []}


@pytest.fixture
def service(tmp_path):
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    cfg['synthesis']['model'] = 'fake'
    FakeASR.calls = FakeLLM.calls = 0
    FakeLLM.fail = False
    return JobService(cfg, FakeASR, FakeLLM)


def test_stage_skip_partial_failure_retry_and_edit(service, tmp_path):
    source = wav(tmp_path / 'note.wav')
    FakeLLM.fail = True
    first = service.run(source, summary=True)
    assert first['status'] == 'partial' and source.with_suffix('.txt').exists()
    assert FakeASR.calls == 1
    FakeLLM.fail = False
    second = service.run(source, summary=True)
    assert second['status'] == 'complete' and FakeASR.calls == 1 and FakeLLM.calls == 2
    third = service.run(source)
    assert third['status'] == 'complete' and FakeLLM.calls == 2
    edited = save_transcript_edit(second['workspace'], {'S00001': 'Inspect 124 किलोमीटर'})
    assert read_json(edited)['raw_revision'] != read_json(edited)['revision']
    fourth = service.run(source)
    assert fourth['status'] == 'complete' and FakeASR.calls == 1 and FakeLLM.calls == 3
    assert '124' in source.with_suffix('.txt').read_text()


def test_protect_unrelated_and_manually_edited_files(service, tmp_path):
    source = wav(tmp_path / 'note.wav')
    output = source.with_suffix('.txt')
    output.write_text('My unrelated note')
    assert service.run(source, summary=False)['status'] == 'partial'
    assert output.read_text() == 'My unrelated note'
    result = service.run(source, output=tmp_path / 'safe', summary=False)
    assert result['status'] == 'complete'
    target = Path(result['outputs'][0])
    target.write_text('My manual edit')
    assert service.run(source, output=tmp_path / 'safe', summary=False)['status'] == 'partial'
    assert target.read_text() == 'My manual edit'


def test_cancellation_and_setting_invalidation(service, tmp_path):
    source = wav(tmp_path / 'note.wav')
    cancel = threading.Event()
    cancel.set()
    assert service.run(source, cancel=cancel)['status'] == 'cancelled'
    assert FakeASR.calls == 0
    assert service.run(source, summary=False)['status'] == 'complete'
    service.settings['audio']['chunk_seconds'] = 30
    assert service.run(source, summary=False)['status'] == 'complete'
    assert FakeASR.calls == 2


def test_bad_evidence_rejected_and_long_input_bounded():
    class Client:
        def generate(self, prompt, schema):
            assert len(prompt.encode()) < 8192
            return {'bottlenecks': [], 'proposals': [{'text': 'Invented', 'kind': 'spoken', 'evidence': ['wrong']}], 'implications': []}
    transcript = {'revision': 'r', 'segments': [{'id': 'S00001', 'text': 'road ' * 8000}]}
    with pytest.raises(AudioToIdeaError, match='evidence'):
        extract(transcript, {'background': '', 'title': 'test', 'output_language': None}, DEFAULTS, Client())


def test_prompt_upgrade_regenerates_ideas_without_repeating_asr(service, tmp_path, monkeypatch):
    import audio_to_idea.jobs as jobs
    import audio_to_idea.synthesis as synthesis
    source = wav(tmp_path / 'note.wav')
    assert service.run(source)['status'] == 'complete'
    first_calls = (FakeASR.calls, FakeLLM.calls)
    version = synthesis.PROMPT_VERSION + 1
    monkeypatch.setattr(synthesis, 'PROMPT_VERSION', version)
    monkeypatch.setattr(jobs, 'PROMPT_VERSION', version)
    assert service.run(source)['status'] == 'complete'
    assert (FakeASR.calls, FakeLLM.calls) == (first_calls[0], first_calls[1] + 1)


def test_watcher_stability_duplicate_and_change(service, tmp_path):
    source = wav(tmp_path / 'note.wav')
    watcher = Watcher(service, tmp_path, summary=False)
    assert watcher.scan(now=0) == []
    assert watcher.scan(now=4) == []
    assert watcher.scan(now=6)[0]['status'] == 'complete'
    assert watcher.scan(now=20) == []
    wav(source, seconds=2)
    assert watcher.scan(now=21) == []
    assert watcher.scan(now=28)[0]['status'] == 'complete'
    assert FakeASR.calls == 2
