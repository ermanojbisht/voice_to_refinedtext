from copy import deepcopy
import json
from unittest.mock import Mock

import pytest
from audio_to_idea.config import DEFAULTS, load_settings
from audio_to_idea.llm import OllamaClient
from audio_to_idea.schemas import AudioToIdeaError
from audio_to_idea.synthesis import extract, render_ideas


def test_stream_options_and_model_capacity(monkeypatch):
    import requests
    cfg = deepcopy(DEFAULTS)
    cfg['synthesis']['model'] = 'local'
    details = Mock()
    details.json.return_value = {'model_info': {'qwen2.context_length': 32768}}
    stream = Mock()
    stream.__enter__ = Mock(return_value=stream)
    stream.__exit__ = Mock()
    stream.iter_lines.return_value = [json.dumps({'response': '{"ok": true}', 'done': True}).encode()]
    request = Mock(side_effect=[details, stream])
    client = OllamaClient(cfg)
    monkeypatch.setattr(client.session, 'post', request)
    assert client.session.trust_env is False
    assert client.generate('prompt', {'type': 'object'}) == {'ok': True}
    payload = request.call_args.kwargs['json']
    assert payload['options']['num_ctx'] == 8192 and payload['options']['temperature'] == .1
    assert 'temperature' not in payload and payload['stream'] is True
    cfg['synthesis']['context_tokens'] = 65536
    client = OllamaClient(cfg)
    client.details = details.json()
    with pytest.raises(AudioToIdeaError, match='capacity'):
        client.validate_runtime()
    client.details = {'remote_host': 'external'}
    with pytest.raises(AudioToIdeaError, match='remote service'):
        client.validate_runtime()


def test_cloud_model_rejected_offline(tmp_path):
    with pytest.raises(AudioToIdeaError, match='Cloud-hosted'):
        load_settings(overrides={'synthesis.model': 'minimax:cloud'}, legacy_path=tmp_path / 'absent')


def test_long_sections_and_evidence_consolidation():
    seen = []
    class Client:
        def generate(self, prompt, schema):
            import re
            assert len(prompt.encode()) < 8192
            ids = list(dict.fromkeys(re.findall(r'\[(S\d+)\]', prompt)))
            seen.extend(ids)
            return {'bottlenecks': [{'text': 'inspection delayed', 'evidence': ids, 'kind': 'spoken'}],
                    'proposals': [], 'implications': []}
    transcript = {'revision': 'r', 'segments': [{'id': f'S{i:05d}', 'text': 'inspection delayed ' * 600} for i in range(1, 8)]}
    ideas = extract(transcript, {'title': 'test', 'background': ''}, DEFAULTS, Client())
    assert len(seen) > 7
    assert ideas['sections']['bottlenecks'][0]['evidence'] == [f'S{i:05d}' for i in range(1, 8)]


def test_spoken_text_must_come_from_cited_source_not_prompt_or_context():
    class Client:
        def generate(self, prompt, schema):
            return {'bottlenecks': [], 'proposals': [{'text': 'Send an engineer on Friday',
                     'kind': 'spoken', 'evidence': ['S00001']}], 'implications': []}
    transcript = {'revision': 'r', 'segments': [{'id': 'S00001', 'text': 'I think you are fine. Copy my words and tell me.'}]}
    with pytest.raises(AudioToIdeaError, match='not in its cited transcript'):
        extract(transcript, {'title': 'Project review', 'background': 'Send an engineer on Friday'}, DEFAULTS, Client())


def test_repeated_finding_across_categories_is_rejected():
    quote = 'The inspection is delayed.'
    class Client:
        def generate(self, prompt, schema):
            return {key: [{'text': quote, 'kind': 'spoken', 'evidence': ['S00001']}]
                    for key in ['bottlenecks', 'proposals', 'implications']}
    with pytest.raises(AudioToIdeaError, match='across categories'):
        extract({'revision': 'r', 'segments': [{'id': 'S00001', 'text': quote}]},
                {'title': 'Project review', 'background': ''}, DEFAULTS, Client())


def test_empty_ideas_are_successful_and_render_concisely():
    class Client:
        def generate(self, prompt, schema):
            return {'bottlenecks': [], 'proposals': [], 'implications': []}
    transcript = {'revision': 'r', 'source_name': 'input.wav', 'duration': 8.704,
                  'segments': [{'id': 'S00001', 'start': 1.36, 'text': 'I think you are fine. Copy my words and tell me.'}]}
    ideas = extract(transcript, {'title': 'Project review', 'background': ''}, DEFAULTS, Client())
    report = render_ideas(ideas, transcript)
    assert 'No actionable ideas identified' in report
    assert len(report.splitlines()) == 4
    assert 'EXECUTIVE' not in report and '###' not in report


def test_report_shows_only_supported_categories():
    transcript = {'revision': 'r', 'source_name': 'inspection.wav', 'duration': 10,
                  'segments': [{'id': 'S00001', 'start': 0, 'text': 'The inspection is delayed.'}]}
    ideas = {'sections': {'bottlenecks': [{'text': 'The inspection is delayed.', 'kind': 'spoken', 'evidence': ['S00001']}],
                         'proposals': [], 'implications': []},
             'context_title': 'Project review', 'transcript_revision': 'r', 'model': 'local'}
    report = render_ideas(ideas, transcript)
    assert 'Core Operational Bottlenecks' in report and 'S00001' in report
    assert 'Actionable Proposals' not in report and 'Regulatory Implications' not in report


def test_category_validation_has_one_bounded_correction():
    quote = 'The inspection is delayed.'
    class Client:
        calls = 0
        def generate(self, prompt, schema):
            self.calls += 1
            item = {'text': quote, 'kind': 'spoken', 'evidence': ['S00001']}
            if self.calls == 1:
                return {'bottlenecks': [item], 'proposals': [item], 'implications': [item]}
            assert 'Validation correction:' in prompt and len(prompt.encode()) < 8192
            return {'bottlenecks': [item], 'proposals': [], 'implications': []}
    client = Client()
    ideas = extract({'revision': 'r', 'segments': [{'id': 'S00001', 'text': quote}]},
                    {'title': 'test', 'background': ''}, DEFAULTS, client)
    assert client.calls == 2
    assert ideas['sections']['bottlenecks'][0]['text'] == quote
    assert not ideas['sections']['implications']


def test_requested_translation_keeps_original_source_quote():
    class Client:
        def generate(self, prompt, schema):
            assert 'quote' in schema['properties']['bottlenecks']['items']['required']
            return {'bottlenecks': [{'text': 'The inspection is delayed.', 'quote': 'निरीक्षण में देरी है।',
                                    'kind': 'spoken', 'evidence': ['S00001']}],
                    'proposals': [], 'implications': []}
    ideas = extract({'revision': 'r', 'segments': [{'id': 'S00001', 'text': 'निरीक्षण में देरी है।'}]},
                    {'title': 'test', 'background': '', 'output_language': 'English'}, DEFAULTS, Client())
    assert ideas['sections']['bottlenecks'][0]['text'] == 'The inspection is delayed.'
