"""Comprehensive Test Matrix for Multi-Language Speech Refinement & Hallucination Prevention.

Verifies:
1. Speech Language Classification (pure English, pure Hindi, mixed Devanagari, Roman Hinglish).
2. Bilingual mode model and prompt routing.
3. Live end-to-end zero-hallucination verification using local Ollama (qwen2.5:3b).
4. PWD Uttarakhand engineering terminology capitalization integrity.
"""
import os
import re
import pytest
from unittest.mock import Mock, patch

import utils
from engine import VoiceEngine


class TestSpeechLanguageClassification:
    """Verifies that speech transcripts are correctly categorized before LLM refinement."""

    def test_pure_english_general_user_case(self):
        text = "This consideration I believe it would be more appropriate to have the system automatically updated and update the manuble to ensure it is always current."
        assert utils.classify_speech_language(text) == "pure_english"
        assert utils.detect_lang(text) == "en"

    def test_pure_english_technical(self):
        text = "The Executive Engineer and Assistant Engineer inspected the bridge pier foundations."
        assert utils.classify_speech_language(text) == "pure_english"
        assert utils.detect_lang(text) == "en"

    def test_pure_hindi_devanagari(self):
        text = "आज हमने सड़क निर्माण कार्य का स्थलीय निरीक्षण किया और संबंधित अधिकारियों को निर्देश दिए।"
        assert utils.classify_speech_language(text) == "pure_hindi"
        assert utils.detect_lang(text) == "hi"

    def test_mixed_devanagari_hinglish(self):
        text = "आज हमने site visit kiya aur EE sahab ne bola ki MB complete hona chahiye."
        assert utils.classify_speech_language(text) == "mixed_devanagari_hinglish"
        assert utils.detect_lang(text) == "hi"

    def test_roman_hinglish_common_words(self):
        text = "Maine aaj site inspect kiya aur EE sahab ko bola ki MB update karein."
        assert utils.classify_speech_language(text) == "roman_hinglish"
        assert utils.detect_lang(text) == "hi"

    def test_roman_hinglish_particles(self):
        text = "Kal subah tender evaluation meeting karni hai aur report bhejna hai."
        assert utils.classify_speech_language(text) == "roman_hinglish"
        assert utils.detect_lang(text) == "hi"

    def test_empty_or_symbol_fallback(self):
        assert utils.classify_speech_language("") == "pure_english"
        assert utils.classify_speech_language("... ??? !!!") == "pure_english"


class TestBilingualRoutingLogic:
    """Verifies that bilingual mode properly routes models based on detected language."""

    @pytest.fixture
    def isolated_engine(self, tmp_path):
        import json
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
            eng = VoiceEngine(str(tmp_path))
            eng.log = Mock()
            return eng

    def test_bilingual_mode_pure_english_selects_en_model(self, isolated_engine, monkeypatch):
        captured = {}
        def mock_call_ollama(host, model, prompt, stops, temp=0.0, **kw):
            captured["model"] = model
            captured["prompt"] = prompt
            return {"response": "Refined English text without Hindi."}

        monkeypatch.setattr(utils, "call_ollama", mock_call_ollama)

        raw = "This consideration I believe it would be more appropriate to have the system automatically updated."
        res = isolated_engine.refine(raw)

        # Must route to English model to prevent hallucinating Hindi/acronyms
        assert captured["model"] == "qwen2.5:3b"
        assert "Refined English text" in res

    def test_bilingual_mode_pure_hindi_selects_hi_model(self, isolated_engine, monkeypatch):
        captured = {}
        def mock_call_ollama(host, model, prompt, stops, temp=0.0, **kw):
            captured["model"] = model
            captured["prompt"] = prompt
            return {"response": "आज हमने निरीक्षण किया।"}

        monkeypatch.setattr(utils, "call_ollama", mock_call_ollama)

        raw = "आज हमने सड़क का निरीक्षण किया"
        res = isolated_engine.refine(raw)

        assert captured["model"] == "llama3-hindi"
        assert "निरीक्षण" in res


class TestLiveOllamaZeroHallucinations:
    """Live verification against local Ollama Qwen2.5:3b model.
    Tests the exact user input that triggered the bug and asserts 0 hallucinations.
    """

    @pytest.fixture
    def real_engine(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with patch("pynput.keyboard.Controller", Mock()):
            eng = VoiceEngine(repo_root)
            eng.log = Mock()
            return eng

    def test_user_exact_failure_case_has_zero_hallucinations(self, real_engine):
        """The exact raw_text from the user's log must refine into clean English.
        Must NOT contain Devanagari, Chinese, or hallucinated PWD abbreviations like (IAR), (REC), (SUS), (MD), (DS).
        """
        raw_text = "This consideration I believe it would be more appropriate to have the system automatically updated and update the manuble to ensure it is always current."

        # Verify classification
        speech_class = utils.classify_speech_language(raw_text)
        assert speech_class == "pure_english"

        # Run through engine.refine
        refined = real_engine.refine(raw_text, mode="bilingual")

        # 1. Must be in English, zero Devanagari characters
        devanagari_matches = re.findall(r"[\u0900-\u097f]", refined)
        assert len(devanagari_matches) == 0, f"Found unexpected Devanagari in pure English refinement: {refined}"

        # 2. Must not contain Chinese characters
        chinese_matches = re.findall(r"[\u4e00-\u9fff]", refined)
        assert len(chinese_matches) == 0, f"Found unexpected Chinese in refinement: {refined}"

        # 3. Must not contain the hallucinated acronyms reported in the bug log
        forbidden_hallucinations = ["(EE)", "(IAR)", "(REC)", "(JE)", "(SUS)", "(MD)", "(MB)", "(SR)", "(DS)"]
        for forbidden in forbidden_hallucinations:
            assert forbidden not in refined, f"Found hallucinated acronym {forbidden} in refined output: {refined}"

        # 4. Spoken typo 'manuble' should be cleaned to 'manual'
        assert "manual" in refined.lower(), f"Expected 'manual' in refined output, got: {refined}"
        assert "current" in refined.lower()

    def test_pwd_acronym_casing_preserved(self, real_engine):
        """Spoken dotted abbreviations like 'e.e.' and 'm.b.' should be cleanly formatted as 'EE' and 'MB'."""
        raw_text = "The e.e. and j.e. reviewed the m.b. for the bridge work."
        refined = real_engine.refine(raw_text, mode="bilingual")
        
        assert "EE" in refined or "Executive Engineer" in refined
        assert "JE" in refined or "Junior Engineer" in refined
        assert "MB" in refined or "Measurement Book" in refined
