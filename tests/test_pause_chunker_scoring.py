"""Comprehensive tests for Handy's Pause-Guided Chunker and Long Dictation Guard.

Validates:
1. Exact mathematical scoring formula with asymmetric penalty (0.05 early vs 0.10 late).
2. Prioritization of full sentence pauses (up to 1.0s) over micro syllable gaps.
3. Fallback RMS minimum energy cut for continuous breath-free speech.
4. Dynamic configuration loading from config.json (zero hardcoding).
5. Integration into engine.transcribe() as a safety guard for long recordings.
"""
import os
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from audio_toolkit.chunker import PauseGuidedChunker, AudioChunk, _load_chunker_config


def test_handy_asymmetric_scoring_formula():
    """Verify Handy's acoustic scoring formula and asymmetric penalty."""
    chunker = PauseGuidedChunker(target_chunk_s=30.0)

    # 1. Exact on-target pause
    # Score = min(gap, 1.0) - 0.0
    score_target = chunker.calculate_candidate_score(gap_duration_s=0.5, position_s=30.0, target_s=30.0)
    assert abs(score_target - 0.5) < 1e-5

    # 2. Asymmetric penalty comparison:
    # 4 seconds early (26.0s): penalty = 0.05 * 4 = 0.20 -> Score = 0.5 - 0.20 = 0.30
    # 4 seconds late (34.0s):  penalty = 0.10 * 4 = 0.40 -> Score = 0.5 - 0.40 = 0.10
    score_early = chunker.calculate_candidate_score(gap_duration_s=0.5, position_s=26.0, target_s=30.0)
    score_late = chunker.calculate_candidate_score(gap_duration_s=0.5, position_s=34.0, target_s=30.0)

    assert abs(score_early - 0.30) < 1e-5
    assert abs(score_late - 0.10) < 1e-5
    assert score_early > score_late, "Early cuts should be penalized less than late cuts (safety bias)"

    # 3. Sentence boundary pause (1.2s) vs micro syllable pause (0.3s) at same distance:
    score_long_pause = chunker.calculate_candidate_score(gap_duration_s=1.2, position_s=29.0, target_s=30.0)
    score_short_pause = chunker.calculate_candidate_score(gap_duration_s=0.3, position_s=29.0, target_s=30.0)
    # Long pause caps at min(1.2, 1.0) = 1.0 - 0.05 = 0.95
    # Short pause = 0.3 - 0.05 = 0.25
    assert abs(score_long_pause - 0.95) < 1e-5
    assert abs(score_short_pause - 0.25) < 1e-5
    assert score_long_pause > score_short_pause


def test_chunker_loads_config_defaults():
    """Verify chunker defaults are loaded dynamically without hardcoding."""
    cfg = _load_chunker_config()
    assert "CHUNK_TARGET_SECONDS" in cfg
    assert "CHUNK_MAX_SECONDS" in cfg
    assert "CHUNK_MIN_SECONDS" in cfg
    assert "CHUNK_MIN_PAUSE_MS" in cfg

    chunker = PauseGuidedChunker()
    assert chunker.target_chunk_s == cfg["CHUNK_TARGET_SECONDS"]
    assert chunker.max_chunk_s == cfg["CHUNK_MAX_SECONDS"]
    assert chunker.min_chunk_s == cfg["CHUNK_MIN_SECONDS"]
    assert chunker.min_pause_ms == cfg["CHUNK_MIN_PAUSE_MS"]


def test_chunker_short_audio_remains_single_piece():
    """Audio shorter than max_chunk_s must never be split."""
    chunker = PauseGuidedChunker(target_chunk_s=30.0, max_chunk_s=40.0)
    pcm = np.zeros(16000 * 20, dtype=np.float32)  # 20s audio
    chunks = chunker.chunk_audio(pcm)
    assert len(chunks) == 1
    assert chunks[0].duration_s == 20.0
    assert chunks[0].index == 0


def test_chunker_candidate_selection_on_synthetic_speech():
    """Synthetic 65s audio with multiple silence pauses. Chunker chooses optimal cut."""
    sr = 16000
    # Create speech block 1 (28s), pause (600ms), speech block 2 (36s)
    speech1 = np.sin(2 * np.pi * 400 * np.linspace(0, 28, 28 * sr)).astype(np.float32) * 0.4
    pause1 = np.zeros(int(0.6 * sr), dtype=np.float32)
    speech2 = np.sin(2 * np.pi * 400 * np.linspace(0, 36, 36 * sr)).astype(np.float32) * 0.4

    audio = np.concatenate([speech1, pause1, speech2])
    total_len = len(audio) / sr

    chunker = PauseGuidedChunker(target_chunk_s=30.0, min_chunk_s=8.0, max_chunk_s=40.0)
    chunks = chunker.chunk_audio(audio)

    assert len(chunks) >= 2
    # Verify the cut occurred right inside the pause (around 28.0s to 28.6s)
    first_chunk_end = chunks[0].end_s
    assert 28.0 <= first_chunk_end <= 28.6
    # Total durations sum up to original
    assert abs(sum(c.duration_s for c in chunks) - total_len) < 0.1


def test_chunker_fallback_continuous_speech():
    """If speech is continuous for 50s without breath pauses, chunker falls back to min RMS energy."""
    sr = 16000
    # Continuous tone with a slightly quieter dip at 30s
    t = np.linspace(0, 50, 50 * sr)
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.5
    # Create a subtle quiet window (dip) at 29-31s
    audio[29 * sr : 31 * sr] *= 0.05

    chunker = PauseGuidedChunker(target_chunk_s=30.0, min_chunk_s=10.0, max_chunk_s=40.0)
    chunks = chunker.chunk_audio(audio)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.duration_s <= 40.0
        assert c.duration_s >= 10.0
    # Cumulative duration matches original
    assert abs(sum(c.duration_s for c in chunks) - 50.0) < 0.1


def test_engine_transcribe_long_audio_guard(tmp_path):
    """Verify engine.transcribe cleanly triggers pause-guided chunking for audio > CHUNK_MAX_SECONDS."""
    from engine import VoiceEngine
    import scipy.io.wavfile as wav

    # Generate 50-second test wav file: 25s voice + 0.5s pause + 24.5s voice
    sr = 16000
    v1 = (np.sin(2 * np.pi * 300 * np.linspace(0, 25, 25 * sr)) * 10000).astype(np.int16)
    p = np.zeros(int(0.5 * sr), dtype=np.int16)
    v2 = (np.sin(2 * np.pi * 300 * np.linspace(0, 24.5, int(24.5 * sr))) * 10000).astype(np.int16)
    pcm = np.concatenate([v1, p, v2])

    test_wav = str(tmp_path / "long_dictation.wav")
    wav.write(test_wav, sr, pcm)

    # Initialize engine with mocked transcribe provider
    engine = VoiceEngine.__new__(VoiceEngine)
    engine.config = {
        "LANGUAGE_MODE": "pure_english",
        "PAUSE_GUIDED_CHUNKING": True,
        "CHUNK_TARGET_SECONDS": 25.0,
        "CHUNK_MAX_SECONDS": 35.0,
        "CHUNK_MIN_SECONDS": 8.0,
        "CHUNK_MIN_PAUSE_MS": 250,
        "FEATURES": {"pwd_terminology_corrector": False},
        "ASR_ENGINE": "mock_asr",
    }
    engine.script_dir = str(tmp_path)
    engine._whisper_model = None

    # Mock asr_provider
    mock_provider = MagicMock()
    mock_provider.transcribe.side_effect = [
        MagicMock(text="First half of long dictation."),
        MagicMock(text="Second half after breath pause."),
    ]
    engine.asr_provider = mock_provider
    engine.get_active_preset = MagicMock(return_value="smart_bilingual")

    result_text = engine.transcribe(test_wav)

    # Both chunks should have been transcribed and joined with space
    assert "First half of long dictation." in result_text
    assert "Second half after breath pause." in result_text
    assert mock_provider.transcribe.call_count == 2
