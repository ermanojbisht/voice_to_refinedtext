from copy import deepcopy
import math
import struct
import wave

import pytest
from audio_to_idea.audio import chunks, command, prepare, probe
from audio_to_idea.config import DEFAULTS
from audio_to_idea.exports import render, timestamp
from audio_to_idea.merging import merge_chunks
from audio_to_idea.storage import file_hash


def wav(path, seconds=1.0, rate=22050):
    with wave.open(str(path), 'wb') as f:
        f.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        f.writeframes(b''.join(struct.pack('<hh', int(1000 * math.sin(i / 10)), 0) for i in range(round(rate * seconds))))
    return path


@pytest.mark.parametrize('duration', [.3, 60, 61.5, 120, 145])
def test_chunk_coverage_and_tail(duration):
    result = list(chunks(duration))
    assert result[0].start == 0 and result[-1].end == duration
    assert all(a.end >= b.start for a, b in zip(result, result[1:]))
    assert all(c.end > c.start for c in result)


@pytest.mark.audio
@pytest.mark.parametrize('normalize', [True, False])
def test_preparation_preserves_input_duration(tmp_path, normalize):
    source = wav(tmp_path / 'quiet आवाज.wav')
    before = file_hash(source)
    cfg = {**DEFAULTS['audio'], 'normalize': normalize}
    folder = tmp_path / 'unique'
    folder.mkdir()
    output, duration = prepare(source, folder, cfg)
    assert file_hash(source) == before
    assert abs(duration - 1) < .02
    info = probe(output)
    assert info['channels'] == 1 and info['sample_rate'] == 16000


def test_overlap_dedup_retains_genuine_repetition():
    def entry(index, words):
        return {'index': index, 'segments': [{'text': 'go go 123', 'start': 1, 'end': 3,
                 'words': [{'text': text, 'start': start, 'end': end} for text, start, end in words]}]}
    chunks_ = [entry(0, [(' go', 1, 1.5), (' go', 1.6, 2), (' 123', 2.2, 2.6)]),
               entry(1, [(' go', 1.61, 2.01), (' 123', 2.21, 2.61), (' done', 2.7, 3)])]
    result, warnings = merge_chunks(chunks_, 4)
    assert ' '.join(s['text'] for s in result) == 'go go 123 done'
    assert not warnings
    assert len({s['id'] for s in result}) == len(result)


def test_hour_timestamps_and_exports():
    assert timestamp(3661.234) == '01:01:01.234'
    data = {'segments': [{'id': 'S00001', 'start': 3661.234, 'end': 3663.5, 'text': '123 किलोमीटर'}]}
    assert '123 किलोमीटर' in render(data, 'txt')
    assert '01:01:01,234 --> 01:01:03,500' in render(data, 'srt')
    assert render(data, 'vtt').startswith('WEBVTT')
    assert 'S00001' in render(data, 'json')


@pytest.mark.audio
@pytest.mark.parametrize('extension', ['mp3', 'm4a', 'aac', 'flac', 'ogg', 'webm'])
def test_supported_container_decoding(tmp_path, extension):
    source = wav(tmp_path / 'source.wav')
    converted = tmp_path / ('voice.' + extension)
    command(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(source), str(converted)])
    output, duration = prepare(converted, tmp_path, DEFAULTS['audio'])
    assert duration > .9 and probe(output)['sample_rate'] == 16000
