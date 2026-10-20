"""Unit tests for the Audio Toolkit (CircularAudioBuffer, SileroVAD, PauseGuidedChunker, StreamRecorder)."""
import os
import time
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from audio_toolkit.ring_buffer import CircularAudioBuffer
from audio_toolkit.silero_vad import SileroVAD
from audio_toolkit.chunker import PauseGuidedChunker, AudioChunk
from audio_toolkit.recorder import StreamRecorder


# ── 1. CircularAudioBuffer Tests ──────────────────────────────────────────────

def test_ring_buffer_init_and_write():
    rb = CircularAudioBuffer(capacity_ms=500, sample_rate=16000)
    assert rb.capacity_samples == 8000
    assert rb.total_written == 0

    # Write 1000 samples
    data = np.ones(1000, dtype=np.float32) * 0.5
    rb.write(data)
    assert rb.total_written == 1000

    pre = rb.get_pre_roll(duration_ms=100)  # 1600 samples
    assert len(pre) == 1000  # Only 1000 available
    assert np.allclose(pre, 0.5)


def test_ring_buffer_wrap_around():
    rb = CircularAudioBuffer(capacity_ms=100, sample_rate=16000)  # 1600 samples capacity
    
    # Write 1000 zeros, then 1000 ones
    rb.write(np.zeros(1000, dtype=np.float32))
    rb.write(np.ones(1000, dtype=np.float32))

    assert rb.total_written == 2000
    # Capacity is 1600. The newest 1000 are 1.0, the remaining 600 are 0.0
    pre = rb.get_pre_roll(duration_ms=100)
    assert len(pre) == 1600
    assert np.allclose(pre[-1000:], 1.0)
    assert np.allclose(pre[:600], 0.0)


def test_ring_buffer_int16_conversion():
    rb = CircularAudioBuffer(capacity_ms=100, sample_rate=16000)
    int16_data = np.array([16384, -16384], dtype=np.int16)
    rb.write(int16_data)

    pre = rb.get_pre_roll(duration_ms=10)
    assert len(pre) == 2
    assert np.allclose(pre, [0.5, -0.5], atol=1e-4)


def test_ring_buffer_clear():
    rb = CircularAudioBuffer(capacity_ms=100, sample_rate=16000)
    rb.write(np.ones(500, dtype=np.float32))
    assert rb.total_written == 500
    rb.clear()
    assert rb.total_written == 0
    pre = rb.get_pre_roll(duration_ms=50)
    assert np.allclose(pre, 0.0)


# ── 2. SileroVAD Tests ────────────────────────────────────────────────────────

def test_silero_vad_silence_detection():
    vad = SileroVAD.get_instance()
    silence = np.zeros(1024, dtype=np.float32)
    prob = vad.speech_probability(silence)
    assert 0.0 <= prob <= 0.15
    assert vad.is_speech(silence) is False


def test_silero_vad_speech_timestamps_on_recordings():
    vad = SileroVAD.get_instance()
    script1_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "benchmarks", "recordings", "script1.wav"
    )
    if not os.path.isfile(script1_path):
        pytest.skip("script1.wav not found")

    import scipy.io.wavfile as wav
    sr, data = wav.read(script1_path)
    pcm = data.astype(np.float32) / 32768.0

    segments = vad.get_speech_timestamps(pcm, sample_rate=sr)
    assert len(segments) >= 1
    assert "start" in segments[0]
    assert "end" in segments[0]
    assert segments[0]["end"] > segments[0]["start"]


# ── 3. PauseGuidedChunker Tests ───────────────────────────────────────────────

def test_chunker_short_audio_single_chunk():
    chunker = PauseGuidedChunker(target_chunk_s=30.0, max_chunk_s=40.0)
    short_audio = np.zeros(16000 * 10, dtype=np.float32)  # 10s audio
    chunks = chunker.chunk_audio(short_audio)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].duration_s == 10.0


def test_chunker_long_audio_with_silence_pauses():
    # Construct a 70-second synthetic audio with speech blocks separated by 500ms pauses
    sr = 16000
    # Create 3 blocks of speech: 25s voice, 0.5s pause, 25s voice, 0.5s pause, 19s voice
    t_v1 = np.sin(2 * np.pi * 300 * np.linspace(0, 25, 25 * sr)).astype(np.float32) * 0.5
    t_p1 = np.zeros(int(0.5 * sr), dtype=np.float32)
    t_v2 = np.sin(2 * np.pi * 300 * np.linspace(0, 25, 25 * sr)).astype(np.float32) * 0.5
    t_p2 = np.zeros(int(0.5 * sr), dtype=np.float32)
    t_v3 = np.sin(2 * np.pi * 300 * np.linspace(0, 19, 19 * sr)).astype(np.float32) * 0.5

    full_audio = np.concatenate([t_v1, t_p1, t_v2, t_p2, t_v3])
    assert len(full_audio) == 70 * sr

    chunker = PauseGuidedChunker(target_chunk_s=30.0, min_chunk_s=10.0, max_chunk_s=40.0)
    chunks = chunker.chunk_audio(full_audio)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.duration_s <= 40.0
        assert c.duration_s >= 5.0
    
    # Cumulative duration equals total audio length
    total_chunked = sum(c.duration_s for c in chunks)
    assert abs(total_chunked - 70.0) < 0.1


# ── 4. StreamRecorder Tests ───────────────────────────────────────────────────

def test_stream_recorder_pre_roll_and_mock_record(tmp_path):
    rec = StreamRecorder(sample_rate=16000, chunk_size=1024, pre_roll_ms=200, silence_dur=0.1, initial_silence_timeout=0.3)
    
    # Pre-populate ring buffer with pre-roll audio
    fake_pre = np.ones(3200, dtype=np.int16) * 1000
    rec.ring_buffer.write(fake_pre)

    out_wav = str(tmp_path / "test_out.wav")

    # Mock sounddevice InputStream to simulate speech then silence
    class MockStream:
        def __init__(self, *args, **kwargs):
            self.count = 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, chunk_size):
            self.count += 1
            if self.count <= 2:
                # 2 chunks of speech
                return np.ones((chunk_size, 1), dtype=np.int16) * 3000, False
            else:
                # Silence chunks
                return np.zeros((chunk_size, 1), dtype=np.int16), False

    # Mock vad speech_probability to return 0.9 for first 2 calls, then 0.0
    call_counts = {"n": 0}
    def mock_speech_prob(chunk):
        call_counts["n"] += 1
        return 0.9 if call_counts["n"] <= 2 else 0.0

    with patch("sounddevice.InputStream", MockStream):
        with patch.object(rec.vad, "speech_probability", side_effect=mock_speech_prob):
            result_path = rec.record(output_wav=out_wav, play_sounds=False)
            assert os.path.isfile(result_path)
            assert result_path == out_wav

            import scipy.io.wavfile as wav
            sr, data = wav.read(result_path)
            assert sr == 16000
            assert len(data) > 0


def test_audio_to_idea_pause_guided_chunks(tmp_path):
    import scipy.io.wavfile as wav
    from audio_to_idea.audio import pause_guided_chunks, Chunk

    test_wav = str(tmp_path / "pause_test.wav")
    sr = 16000
    # 8-second audio
    data = (np.sin(2 * np.pi * 300 * np.linspace(0, 8, 8 * sr)) * 10000).astype(np.int16)
    wav.write(test_wav, sr, data)

    chunks = list(pause_guided_chunks(test_wav, target_seconds=5.0, min_chunk_seconds=2.0, max_chunk_seconds=10.0))
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)
    assert chunks[0].index == 0
    assert chunks[0].start == 0.0

