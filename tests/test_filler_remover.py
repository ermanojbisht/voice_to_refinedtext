"""Unit tests for Microsecond Filler Word Remover (pwd_helper/filler.py)."""
import pytest
from pwd_helper.filler import FillerWordRemover


def test_universal_fillers_removal():
    remover = FillerWordRemover()
    raw = "We should, uh, inspect the bridge pier and, umm, verify RD 14."
    cleaned = remover.clean(raw)
    assert "uh" not in cleaned
    assert "umm" not in cleaned
    assert "inspect the bridge pier and" in cleaned


def test_capitalization_debt_handover():
    remover = FillerWordRemover()
    raw = "Um, the software engineering team should automate the pipeline."
    cleaned = remover.clean(raw)
    assert cleaned.startswith("The software engineering team")
    assert not cleaned.startswith("the")


def test_mid_sentence_capitalization_preservation():
    remover = FillerWordRemover()
    raw = "The report is ready. Um, we should submit it to EE sir."
    cleaned = remover.clean(raw)
    assert "The report is ready. We should submit it to EE sir." in cleaned


def test_stutter_collapsing():
    remover = FillerWordRemover(collapse_stutters_enabled=True)
    raw = "I I I I believe the the the estimate is accurate."
    cleaned = remover.clean(raw)
    assert cleaned == "I believe the estimate is accurate."


def test_stutter_collapsing_disabled():
    remover = FillerWordRemover(collapse_stutters_enabled=False)
    raw = "I I I I believe"
    cleaned = remover.clean(raw)
    assert cleaned == "I I I I believe"


def test_hindi_fillers_and_lexical_preservation():
    remover = FillerWordRemover()
    # Filler position: clause-opening 'मतलब,'
    raw_filler = "मतलब, साइट इंस्पेक्शन के दौरान काम पूरा हो चुका था।"
    cleaned_filler = remover.clean(raw_filler, language="hi")
    assert "मतलब" not in cleaned_filler
    assert "साइट इंस्पेक्शन के दौरान" in cleaned_filler

    # Lexical noun position: 'मतलब' must be preserved!
    raw_lexical = "इस शब्द का मतलब क्या है?"
    cleaned_lexical = remover.clean(raw_lexical, language="hi")
    assert "मतलब" in cleaned_lexical
    assert cleaned_lexical == "इस शब्द का मतलब क्या है?"


def test_english_gated_fillers():
    remover = FillerWordRemover()
    raw = "The project is, you know, slightly delayed, I mean, due to rain."
    cleaned = remover.clean(raw, language="en")
    assert "you know" not in cleaned
    assert "I mean" not in cleaned
    assert "The project is slightly delayed due to rain." in cleaned or "The project is, slightly delayed, due to rain." in cleaned


def test_disabled_returns_untouched_verbatim():
    remover = FillerWordRemover()
    raw = "Um, uh, you know, I I I think..."
    cleaned = remover.clean(raw, enabled=False)
    assert cleaned == raw


def test_custom_filler_words():
    remover = FillerWordRemover(custom_fillers=["basically", "literally"])
    raw = "The bridge is basically complete and literally inspected."
    cleaned = remover.clean(raw)
    assert "basically" not in cleaned
    assert "literally" not in cleaned
    assert "The bridge is complete and inspected." in cleaned


def test_engine_transcribe_filler_removal_integration():
    from engine import VoiceEngine
    from audio_to_idea.asr.base import BaseASRProvider, ASRResult

    class MockASR(BaseASRProvider):
        def load(self): pass
        def close(self): pass
        def is_available(self): return True
        def transcribe(self, pcm, **kwargs):
            text = "Um, the contractor submitted, uh, the revised MB today."
            return ASRResult(text=text, language="en", duration=2.0, latency_ms=10.0, segments=[], backend="mock")

    eng = VoiceEngine(".")
    eng.asr_provider = MockASR()

    # Enabled
    eng.config["ENABLE_FILLER_REMOVAL"] = True
    eng.config["FEATURES"]["filler_word_removal"] = True
    cleaned = eng.transcribe("input.wav")
    assert "Um," not in cleaned
    assert "uh," not in cleaned
    assert "The contractor submitted" in cleaned

    # Disabled
    eng.config["ENABLE_FILLER_REMOVAL"] = False
    raw = eng.transcribe("input.wav")
    assert "Um, the contractor" in raw
    assert "uh," in raw
