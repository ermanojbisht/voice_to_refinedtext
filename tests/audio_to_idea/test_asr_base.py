"""Unit tests for BaseASRProvider, dataclasses, and ASRFactory."""
import numpy as np
import pytest

from audio_to_idea.asr import (
    ASRFactory,
    ASRResult,
    ASRSegment,
    ASRWord,
    BaseASRProvider,
    FasterWhisperProvider,
    HandyCliProvider,
    TranscribeCppProvider,
)


class MockASRProvider(BaseASRProvider):
    def __init__(self, output_text="mocked speech", language="en"):
        self.output_text = output_text
        self.language = language
        self.loaded = False
        self.closed = False

    def load(self):
        self.loaded = True

    def transcribe(self, pcm, *, language=None, prompt=None, **kwargs):
        duration = len(pcm) / 16000.0 if len(pcm) > 0 else 0.0
        return ASRResult(
            text=self.output_text,
            language=language or self.language,
            duration=duration,
            latency_ms=10.0,
            segments=[
                ASRSegment(
                    id="S00001",
                    text=self.output_text,
                    start=0.0,
                    end=duration,
                    words=[ASRWord(text=w, start=0.0, end=duration) for w in self.output_text.split()],
                )
            ],
            backend="mock",
            model_path="mock://model",
        )

    def close(self):
        self.closed = True


def test_asr_data_models():
    word = ASRWord(text="hello", start=0.0, end=0.5, probability=0.98)
    assert word.text == "hello"
    assert word.probability == 0.98

    seg = ASRSegment(id="S00001", text="hello world", start=0.0, end=1.0, words=[word])
    assert seg.id == "S00001"
    assert len(seg.words) == 1

    res = ASRResult(
        text="hello world",
        language="en",
        duration=1.0,
        latency_ms=15.0,
        segments=[seg],
        backend="test",
        model_path="test_model",
    )
    assert res.text == "hello world"
    assert res.latency_ms == 15.0


def test_mock_provider_lifecycle():
    prov = MockASRProvider("testing lifecycle", language="hi")
    pcm = np.zeros(16000 * 2, dtype=np.float32)

    prov.load()
    assert prov.loaded is True

    result = prov.transcribe(pcm)
    assert result.text == "testing lifecycle"
    assert result.duration == 2.0
    assert result.language == "hi"

    prov.close()
    assert prov.closed is True


def test_asr_factory_default_fallback():
    # If no config provided, defaults to FasterWhisperProvider
    prov = ASRFactory.from_engine_config({})
    assert isinstance(prov, FasterWhisperProvider)
    assert prov.model_path_or_id == "large-v3-turbo"


def test_asr_factory_transcribe_cpp_resolution():
    cfg = {
        "ASR_ENGINE": "transcribe_cpp",
        "ACTIVE_MODEL_PROFILE": "nemotron_fast",
        "MODEL_PROFILES": {
            "nemotron_fast": {
                "backend": "transcribe_cpp",
                "family": "nemotron",
                "path": "/media/manoj/F1/models-handy/nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf",
            }
        },
    }
    prov = ASRFactory.from_engine_config(cfg)
    # If file exists and transcribe-cpp is installed, returns TranscribeCppProvider
    if prov.is_available():
        assert isinstance(prov, TranscribeCppProvider)
        assert prov.model_path.endswith("nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf")


def test_asr_factory_handy_cli():
    cfg = {
        "ASR_ENGINE": "handy_cli",
        "ACTIVE_MODEL_PROFILE": "handy_default",
        "MODEL_PROFILES": {"handy_default": {"backend": "handy_cli"}},
    }
    prov = ASRFactory.from_engine_config(cfg)
    if prov.is_available():
        assert isinstance(prov, HandyCliProvider)


def test_asr_factory_from_settings():
    settings = {
        "asr": {
            "backend": "faster-whisper",
            "model_id": "Systran/faster-whisper-tiny",
            "device": "cpu",
            "compute_type": "int8",
        }
    }
    prov = ASRFactory.from_settings(settings)
    assert isinstance(prov, FasterWhisperProvider)
    assert prov.model_path_or_id == "Systran/faster-whisper-tiny"
    assert prov.requested_device == "cpu"
