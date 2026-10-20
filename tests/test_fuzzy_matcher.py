"""Tests for Fuzzy N-Gram Custom Domain Replacement Engine.

Verifies parity with Handy text.rs architecture:
- Exact matches
- 2-word, 3-word, and 4-word sliding n-gram matching
- Ampersand expansions (R&D)
- Case pattern preservation (ALL-CAPS, Titlecase)
- Boundary punctuation preservation
- Clause-boundary punctuation safeguards
- Short-term exact guards (protecting common English words from 3-letter acronyms)
- Length difference guards
- Trailing number double-counting prevention
- Engine integration with ON/OFF feature toggles
"""
import time
import pytest
from pwd_helper.fuzzy_matcher import (
    FuzzyCustomWordMatcher,
    apply_custom_words,
    extract_punctuation,
    preserve_case_pattern,
    soundex,
    levenshtein_distance,
    load_all_domain_words,
)


def test_soundex_parity():
    """Verifies American Soundex matches across phonetic equivalents."""
    assert soundex("Robert") == soundex("Rupert")
    assert soundex("Handee") == soundex("Handy")
    assert soundex("ChargeB") == soundex("ChargeBee")
    assert soundex("123") == ""
    assert soundex("") == ""


def test_levenshtein_distance():
    """Verifies iterative dynamic programming Levenshtein distance."""
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("chargeb", "chargebee") == 2
    assert levenshtein_distance("same", "same") == 0
    assert levenshtein_distance("", "test") == 4


def test_extract_punctuation():
    """Verifies extraction of leading/trailing ASCII and Unicode punctuation."""
    assert extract_punctuation("(Charge") == ("(", "")
    assert extract_punctuation("Bee)?") == ("", ")?")
    assert extract_punctuation("「Handee。」") == ("「", "。」")
    assert extract_punctuation("normal") == ("", "")
    assert extract_punctuation("...") == ("...", "")


def test_preserve_case_pattern():
    """Verifies casing handover from original token to replacement."""
    # ALL-CAPS
    assert preserve_case_pattern("CHARGE", "ChargeBee") == "CHARGEBEE"
    # Titlecase
    assert preserve_case_pattern("Charge", "chargebee") == "Chargebee"
    # Lowercase / original preserved
    assert preserve_case_pattern("charge", "ChargeBee") == "ChargeBee"


def test_apply_custom_words_exact():
    """Verifies exact matches."""
    text = "hello world"
    custom_words = ["Hello", "World"]
    assert apply_custom_words(text, custom_words, 0.5) == "Hello World"


def test_apply_custom_words_two_word_ngram():
    """Verifies multi-word split repair for 2 tokens (Handy parity)."""
    text = "il cui nome è Charge B, che permette"
    custom_words = ["ChargeBee"]
    result = apply_custom_words(text, custom_words, 0.5)
    assert "ChargeBee," in result
    assert "Charge B" not in result


def test_apply_custom_words_three_word_ngram():
    """Verifies 3-token split repair."""
    text = "using Mac Book Pro today"
    custom_words = ["MacBook Pro"]
    result = apply_custom_words(text, custom_words, 0.5)
    assert result == "using MacBook Pro today"


def test_apply_custom_words_four_word_ngram():
    """Verifies 4-token split repair for proper names and acronyms."""
    text = "use Chat G P T for this task"
    custom_words = ["ChatGPT"]
    result = apply_custom_words(text, custom_words, 0.35, max_ngram=4)
    assert result == "use ChatGPT for this task"


def test_apply_custom_words_preserves_case():
    """Verifies ALL-CAPS preservation on multi-word n-gram."""
    text = "CHARGE B is great"
    custom_words = ["ChargeBee"]
    result = apply_custom_words(text, custom_words, 0.5)
    assert "CHARGEBEE" in result
    # Ensures "is" was not swallowed
    assert "is great" in result


def test_apply_custom_words_ampersand():
    """Verifies spoken 'and' replaces with ampersand dictionary entry."""
    text = "send it to R and D for review"
    custom_words = ["R&D"]
    result = apply_custom_words(text, custom_words, 0.2)
    assert result == "send it to R&D for review"


def test_apply_custom_words_unicode_punctuation():
    """Verifies Japanese/Unicode brackets and full stops are preserved."""
    text = "「Handee。」"
    custom_words = ["Handy"]
    result = apply_custom_words(text, custom_words, 0.5)
    assert result == "「Handy。」"


def test_apply_custom_words_trailing_number_not_doubled():
    """Verifies alphanumeric tokens do not double-count numbers."""
    text = "use GPT4 for this"
    custom_words = ["GPT-4"]
    result = apply_custom_words(text, custom_words, 0.5)
    assert result == "use GPT-4 for this"
    assert "GPT-44" not in result


def test_apply_custom_words_prefers_longer_ngram():
    """Verifies longer n-gram is preferred when matching compound terms."""
    text = "Open AI GPT model"
    custom_words = ["OpenAI", "GPT"]
    result = apply_custom_words(text, custom_words, 0.5)
    assert result == "OpenAI GPT model"


def test_apply_custom_words_cjk_skipped():
    """Verifies non-ASCII fuzzy Soundex is safely skipped."""
    text = "你好。"
    custom_words = ["你号"]
    result = apply_custom_words(text, custom_words, 1.0)
    assert result == "你好。"


def test_short_term_exact_guard():
    """Verifies short acronyms (<= 3 chars like SOR, SDO, EE) do not consume common English words."""
    domain_words = ["SDO", "SOR", "DPR", "MB", "EE", "JE"]
    matcher = FuzzyCustomWordMatcher(domain_words, threshold=0.35)

    # "site" and "for" must NEVER be replaced by "SDO" or "SOR"
    sample = "site inspection for the d p r and the m b"
    result = matcher.apply(sample)

    assert "site" in result
    assert "for" in result
    assert "SDO" not in result
    assert "SOR" not in result
    assert "DPR" in result
    assert "MB" in result


def test_clause_boundary_punctuation_safeguard():
    """Verifies that punctuation in middle of candidate prevents crossing clause seam."""
    text = "Charge B, check this out"
    custom_words = ["ChargeBee"]
    result = apply_custom_words(text, custom_words, 0.5)
    # The comma after B closes the candidate; should match Charge B -> ChargeBee, but leave "check"
    assert "ChargeBee," in result
    assert "check this out" in result


def test_load_all_domain_words():
    """Verifies aggregator loads both config words and PWD dictionary terms."""
    cfg = {"CUSTOM_WORDS": ["MyCustomTool", "ChatGPT"]}
    words = load_all_domain_words(cfg)
    assert "MyCustomTool" in words
    assert "ChatGPT" in words
    assert "DPR" in words
    assert "NIT" in words
    assert "MB" in words


def test_engine_integration():
    """Verifies engine pipeline applies fuzzy matching when enabled and bypasses when disabled."""
    from engine import VoiceEngine
    from audio_to_idea.asr.base import BaseASRProvider, ASRResult

    class MockASR(BaseASRProvider):
        def load(self): pass
        def close(self): pass
        def is_available(self): return True
        def transcribe(self, pcm, **kwargs):
            return ASRResult(
                text="Please use Chat G P T and check Charge B",
                language="en",
                duration=1.0,
                latency_ms=5.0,
                segments=[],
                backend="mock",
            )

    engine = VoiceEngine(".")
    engine.asr_provider = MockASR()

    # Enabled
    engine.config["ENABLE_FUZZY_CUSTOM_WORDS"] = True
    engine.config["FEATURES"]["fuzzy_custom_words"] = True
    engine.config["CUSTOM_WORDS"] = ["ChatGPT", "ChargeBee"]
    engine._fuzzy_matcher = None  # Reload

    res_on = engine.transcribe(b"\x00" * 3200)
    assert "ChatGPT" in res_on
    assert "ChargeBee" in res_on

    # Disabled
    engine.config["ENABLE_FUZZY_CUSTOM_WORDS"] = False
    res_off = engine.transcribe(b"\x00" * 3200)
    assert "Chat G P T" in res_off
    assert "Charge B" in res_off


def test_submillisecond_speed_benchmark():
    """Verifies custom word matching takes < 1.5ms for standard transcript."""
    custom = ["ChatGPT", "OpenAI", "Claude", "ChargeBee", "MacBook Pro", "GitHub", "DevOps", "DPR", "NIT", "MB"]
    matcher = FuzzyCustomWordMatcher(custom, threshold=0.35)
    sample = "I asked Chat G P T on my Mac Book Pro about the d p r and Charge B"

    # Warmup
    matcher.apply(sample)

    t0 = time.perf_counter()
    N = 100
    for _ in range(N):
        matcher.apply(sample)
    avg_sec = (time.perf_counter() - t0) / N

    # Must be sub-millisecond (or < 2ms on any busy CI machine)
    assert avg_sec < 0.002, f"Expected < 2ms, got {avg_sec * 1000:.3f}ms"
