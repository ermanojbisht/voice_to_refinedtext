"""Unit and regression tests for Multilingual Refinement & 4-Mode Language Selection."""
import os
import json
import types
from unittest.mock import Mock, patch
import pytest

import utils
from engine import VoiceEngine


@pytest.fixture
def mock_engine(tmp_path):
    """Creates a VoiceEngine with isolated test directory and mock controller."""
    cfg = {
        "SAMPLE_RATE": 16000,
        "LANGUAGE_MODE": "bilingual",
        "MODE": "refine",
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_MODELS": {
            "en": "qwen2.5:3b",
            "hi": "llama3-hindi"
        },
        "OLLAMA_TRANSLATE_MODELS": {
            "to_en": "qwen2.5:3b",
            "to_hi": "llama3-hindi"
        },
        "FEATURES": {
            "pwd_terminology_corrector": True
        }
    }
    (tmp_path / "config.json").write_text(json.dumps(cfg))
    
    with patch("pynput.keyboard.Controller", Mock()):
        engine = VoiceEngine(str(tmp_path))
        engine.log = Mock()
        return engine


def test_prompt_template_discovery(tmp_path):
    """Verify get_prompt_and_stops finds the 4 new mode templates."""
    script_dir = str(tmp_path)
    prompts_dir = tmp_path / "prompts" / "default"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    (prompts_dir / "bilingual.txt").write_text("BILINGUAL: {text}")
    (prompts_dir / "pure_english.txt").write_text("ENGLISH: {text}")
    (prompts_dir / "pure_hindi.txt").write_text("HINDI: {text}")
    (prompts_dir / "roman_hinglish.txt").write_text("HINGLISH: {text}")
    
    # Test bilingual
    p1, _ = utils.get_prompt_and_stops(script_dir, "qwen2.5:3b", "test audio", "en", mode="bilingual")
    assert "BILINGUAL: test audio" in p1
    
    # Test pure_english
    p2, _ = utils.get_prompt_and_stops(script_dir, "qwen2.5:3b", "test audio", "en", mode="pure_english")
    assert "ENGLISH: test audio" in p2
    
    # Test pure_hindi
    p3, _ = utils.get_prompt_and_stops(script_dir, "llama3-hindi", "test audio", "hi", mode="pure_hindi")
    assert "HINDI: test audio" in p3
    
    # Test roman_hinglish
    p4, _ = utils.get_prompt_and_stops(script_dir, "qwen2.5:3b", "test audio", "en", mode="roman_hinglish")
    assert "HINGLISH: test audio" in p4


def test_refine_routes_bilingual_mode(mock_engine, monkeypatch):
    """Verify default bilingual mode passes mode='bilingual' and cleans response."""
    mock_engine.config["LANGUAGE_MODE"] = "bilingual"
    monkeypatch.setattr(utils, "detect_lang", lambda _: "en")
    
    captured = {}
    def mock_get_prompt_and_stops(script_dir, model_name, text, lang, mode="refine", config=None):
        captured["mode"] = mode
        captured["model_name"] = model_name
        return ("prompt", [])
    
    monkeypatch.setattr(utils, "get_prompt_and_stops", mock_get_prompt_and_stops)
    monkeypatch.setattr(utils, "call_ollama", lambda *a, **kw: {"response": "आज हमने site inspect किया और ee ने nit issue किया।"})
    
    res = mock_engine.refine("sample speech")
    assert captured["mode"] == "bilingual"
    # Verify PWD normalizer capitalized ee -> EE and nit -> NIT
    assert "EE" in res
    assert "NIT" in res


def test_refine_routes_pure_english_mode(mock_engine, monkeypatch):
    """Verify pure_english mode selects English model and pure_english prompt."""
    mock_engine.config["LANGUAGE_MODE"] = "pure_english"
    monkeypatch.setattr(utils, "detect_lang", lambda _: "hi")
    
    captured = {}
    def mock_get_prompt_and_stops(script_dir, model_name, text, lang, mode="refine", config=None):
        captured["mode"] = mode
        captured["model_name"] = model_name
        return ("prompt", [])
    
    monkeypatch.setattr(utils, "get_prompt_and_stops", mock_get_prompt_and_stops)
    monkeypatch.setattr(utils, "call_ollama", lambda *a, **kw: {"response": "Today we inspected the site."})
    
    res = mock_engine.refine("आज हमने साइट का निरीक्षण किया")
    assert captured["mode"] == "pure_english"
    assert captured["model_name"] == "qwen2.5:3b"
    assert res == "Today we inspected the site."


def test_refine_routes_pure_hindi_mode(mock_engine, monkeypatch):
    """Verify pure_hindi mode selects Hindi model and pure_hindi prompt."""
    mock_engine.config["LANGUAGE_MODE"] = "pure_hindi"
    monkeypatch.setattr(utils, "detect_lang", lambda _: "en")
    
    captured = {}
    def mock_get_prompt_and_stops(script_dir, model_name, text, lang, mode="refine", config=None):
        captured["mode"] = mode
        captured["model_name"] = model_name
        return ("prompt", [])
    
    monkeypatch.setattr(utils, "get_prompt_and_stops", mock_get_prompt_and_stops)
    monkeypatch.setattr(utils, "call_ollama", lambda *a, **kw: {"response": "कृपया bridge का status चेक करें।"})
    
    res = mock_engine.refine("Please check the status of bridge.")
    assert captured["mode"] == "pure_hindi"
    assert captured["model_name"] == "llama3-hindi"
    assert "bridge" in res


def test_legacy_mode_translate_backward_compatibility(mock_engine, monkeypatch):
    """Verify caller explicitly passing mode='translate' continues to work seamlessly."""
    monkeypatch.setattr(utils, "detect_lang", lambda _: "hi")
    
    captured = {}
    def mock_get_prompt_and_stops(script_dir, model_name, text, lang, mode="refine", config=None):
        captured["mode"] = mode
        captured["model_name"] = model_name
        return ("prompt", [])
    
    monkeypatch.setattr(utils, "get_prompt_and_stops", mock_get_prompt_and_stops)
    monkeypatch.setattr(utils, "call_ollama", lambda *a, **kw: {"response": "Translated text"})
    
    res = mock_engine.refine("नमस्ते", mode="translate")
    assert captured["mode"] == "translate"
    assert captured["model_name"] == "qwen2.5:3b"
    assert res == "Translated text"


def test_whisper_pure_english_forces_language_en(mock_engine):
    """Verify that pure_english mode constrains Whisper transcribe to language='en'."""
    mock_engine.config["LANGUAGE_MODE"] = "pure_english"
    
    mock_whisper = Mock()
    mock_whisper.transcribe.return_value = (
        iter([types.SimpleNamespace(text="Hello world", no_speech_prob=0.0)]),
        types.SimpleNamespace(language="en")
    )
    mock_engine._whisper_model = mock_whisper
    
    text = mock_engine.transcribe("fake.wav")
    assert text == "Hello world"
    assert mock_whisper.transcribe.call_count == 1
    assert mock_whisper.transcribe.call_args.kwargs.get("language") == "en"
    assert "civil works" in mock_whisper.transcribe.call_args.kwargs.get("initial_prompt")


def test_whisper_pure_hindi_forces_language_hi(mock_engine):
    """Verify that pure_hindi mode constrains Whisper transcribe to language='hi' with Hindi prompt."""
    mock_engine.config["LANGUAGE_MODE"] = "pure_hindi"
    
    mock_whisper = Mock()
    mock_whisper.transcribe.return_value = (
        iter([types.SimpleNamespace(text="नमस्ते काम पूरा हो गया", no_speech_prob=0.0)]),
        types.SimpleNamespace(language="hi")
    )
    mock_engine._whisper_model = mock_whisper
    
    text = mock_engine.transcribe("fake.wav")
    assert text == "नमस्ते काम पूरा हो गया"
    assert mock_whisper.transcribe.call_count == 1
    assert mock_whisper.transcribe.call_args.kwargs.get("language") == "hi"
    assert mock_whisper.transcribe.call_args.kwargs.get("initial_prompt") == mock_engine._HINDI_PROMPT


def test_qwen_model_prompt_has_phonetic_recovery():
    """Verify real prompt for qwen2.5_3b contains phonetic recovery rule for Devanagari ASR."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt, _ = utils.get_prompt_and_stops(repo_root, "qwen2.5:3b", "sample text", "hi", mode="pure_english")
    assert "PHONETIC & SCRIPT RECOVERY RULE" in prompt
    assert "Devanagari" in prompt


def test_llama3_hindi_model_prompt_is_devanagari():
    """Verify real prompt for llama3_hindi contains Devanagari instructions to prevent English over-translation."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt, _ = utils.get_prompt_and_stops(repo_root, "llama3_hindi", "sample text", "hi", mode="bilingual")
    assert "बोली गई भाषा का मिश्रण बनाए रखें" in prompt
    assert "अनुवाद न करें" in prompt

