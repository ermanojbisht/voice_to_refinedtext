"""Integration test for TranscribeCppProvider with Nemotron GGUF model."""
import os
import numpy as np
import pytest
import scipy.io.wavfile as wav_io

from audio_to_idea.asr import TranscribeCppProvider

NEMOTRON_PATH = "/media/manoj/F1/models-handy/nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf"
INPUT_WAV = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "input.wav")


@pytest.mark.skipif(not os.path.isfile(NEMOTRON_PATH), reason="Nemotron GGUF model not present")
@pytest.mark.skipif(not os.path.isfile(INPUT_WAV), reason="input.wav test audio not present")
def test_transcribe_cpp_nemotron_inference():
    prov = TranscribeCppProvider(model_path=NEMOTRON_PATH)
    assert prov.is_available() is True

    # Read test WAV
    sr, data = wav_io.read(INPUT_WAV)
    if data.dtype == np.int16:
        pcm = data.astype(np.float32) / 32768.0
    else:
        pcm = data.astype(np.float32)

    if len(pcm.shape) > 1:
        pcm = pcm.mean(axis=1)

    prov.load()

    # Warm run
    res1 = prov.transcribe(pcm)
    assert res1.text != ""
    assert res1.duration > 0.0
    assert len(res1.segments) > 0

    # Fast warm run: real-time factor should be well under 0.1x (faster than 10x real-time)
    res2 = prov.transcribe(pcm)
    assert res2.text == res1.text
    assert res2.latency_ms < max(1000.0, res2.duration * 50.0)  # > 20x faster than real-time

    prov.close()
