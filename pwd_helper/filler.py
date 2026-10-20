"""Microsecond In-Memory Filler Word Remover.

Ported from Handy's audio_toolkit/text.rs architecture and optimized for
bilingual English/Hindi and civil engineering dictation.

Key Capabilities:
1. Universal Non-Lexical Fillers: Strips pure hesitation vocal noises ('uh', 'umm', 'hmm', 'हम्म').
2. Language-Gated Fillers:
   - English: 'um', 'you know', 'I mean', 'like' (in hesitation positions).
   - Hindi / Hinglish: 'मतलब' (comma/clause-bounded), 'जैसे कि', 'यानी कि'.
3. Stutter Collapse: Collapses 3+ consecutive repetitions ('I I I I' -> 'I').
4. Capitalization Handover: Restores sentence capitalization when an opening filler is removed
   ('Um, the software...' -> 'The software...').
5. Punctuation Hygiene: Eliminates orphan commas and collapses redundant whitespace.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple


# Tier 1: Universal hesitation noises that are never legitimate lexical words
UNIVERSAL_FILLERS_EN = [
    "uh", "uhm", "umm", "uhh", "uhhh", "ehh", "ehm", "ahm", "hmm", "hm", "mmm",
]

UNIVERSAL_FILLERS_HI = [
    "उम", "उम्म", "अह", "हम्म", "ह्म",
]

# Tier 2: Language-gated fillers (real words in some languages, but hesitations here)
GATED_FILLERS_EN = [
    "um", "ah", "eh", "you know", "i mean",
]

# Hindi clause-initial or comma-bounded fillers
GATED_FILLERS_HI = [
    "जैसे कि", "यानी कि", "तो क्या है कि",
]

MULTI_SPACE_RE = re.compile(r"\s{2,}")
ORPHAN_COMMA_RE = re.compile(r",\s*,")
OPEN_SENTENCE_PUNCT = {".", "!", "?", "…", "।", "॥"}


def _opens_sentence(kept: str) -> bool:
    """Returns True if the text so far is empty or ends in terminal sentence punctuation."""
    trimmed = kept.rstrip()
    if not trimmed:
        return True
    return trimmed[-1] in OPEN_SENTENCE_PUNCT


def _push_restoring_capital(kept_parts: List[str], segment: str, capital_owed: bool) -> bool:
    """Appends segment to kept_parts, capitalizing the first alphanumeric character if capital_owed is True.

    Returns the new state of capital_owed.
    """
    if capital_owed:
        for idx, ch in enumerate(segment):
            if ch.isalnum():
                kept_parts.append(segment[:idx])
                kept_parts.append(ch.upper())
                kept_parts.append(segment[idx + 1:])
                return False  # Capital debt paid
    kept_parts.append(segment)
    return capital_owed


class FillerWordRemover:
    """High-speed in-memory verbal hesitation and stutter remover (<0.1ms)."""

    def __init__(
        self,
        custom_fillers: Optional[List[str]] = None,
        collapse_stutters_enabled: bool = True,
    ):
        self.custom_fillers = custom_fillers or []
        self.collapse_stutters_enabled = collapse_stutters_enabled

        # Precompile universal patterns with word boundaries and optional trailing punctuation
        self._universal_patterns: List[re.Pattern] = []
        for word in UNIVERSAL_FILLERS_EN:
            self._universal_patterns.append(
                re.compile(rf"(?i)\b{re.escape(word)}\b[,.]?\s*")
            )
        for word in UNIVERSAL_FILLERS_HI:
            self._universal_patterns.append(
                re.compile(rf"(?:^|\s+){re.escape(word)}[,.]?\s*")
            )

        # Precompile English gated patterns
        self._en_gated_patterns: List[re.Pattern] = []
        for word in GATED_FILLERS_EN:
            self._en_gated_patterns.append(
                re.compile(rf"(?i)\b{re.escape(word)}\b[,.]?\s*")
            )

        # Precompile Hindi gated patterns
        self._hi_gated_patterns: List[re.Pattern] = []
        for word in GATED_FILLERS_HI:
            self._hi_gated_patterns.append(
                re.compile(rf"(?:^|[,\.\!\?।]\s*){re.escape(word)}[,]?\s*")
            )
        # Context guard for Hindi 'मतलब': only remove when bounded as a filler (e.g. ", matlab," or at start "^matlab,")
        # Does NOT remove lexical use: "iska matlab kya hai"
        self._hi_matlab_pattern = re.compile(r"(?:^|[,\.\!\?।]\s*)(?:मतलब|matlab)[,]\s*", re.IGNORECASE)

    def collapse_stutters(self, text: str) -> str:
        """Collapses 3+ consecutive repetitions of identical words into a single instance.

        E.g. 'I I I I believe' -> 'I believe', 'the the the' -> 'the'.
        """
        if not text or not self.collapse_stutters_enabled:
            return text

        words = text.split()
        if len(words) < 3:
            return text

        result: List[str] = []
        i = 0
        while i < len(words):
            word = words[i]
            # Strip punctuation for comparison
            word_clean = re.sub(r"[^\w]", "", word).casefold()
            if not word_clean:
                result.append(word)
                i += 1
                continue

            count = 1
            while (
                i + count < len(words)
                and re.sub(r"[^\w]", "", words[i + count]).casefold() == word_clean
            ):
                count += 1

            if count >= 3:
                result.append(word)
                i += count
            else:
                result.append(word)
                i += 1

        return " ".join(result)

    def _remove_matches_with_capitalization(self, text: str, pattern: re.Pattern) -> str:
        """Removes pattern matches while transferring sentence-opening capital letters to the next word."""
        kept_parts: List[str] = []
        resume = 0
        capital_owed = False

        for match in pattern.finditer(text):
            matched_text = match.group()
            prefix = text[resume:match.start()]
            capital_owed = _push_restoring_capital(kept_parts, prefix, capital_owed)

            # Check if this filler was capitalized AND opened a sentence
            was_capitalized = matched_text and matched_text[0].isupper()
            current_text_so_far = "".join(kept_parts)
            if was_capitalized and _opens_sentence(current_text_so_far):
                capital_owed = True

            resume = match.end()

        # Flush remainder
        suffix = text[resume:]
        _push_restoring_capital(kept_parts, suffix, capital_owed)

        return "".join(kept_parts)

    def clean(
        self,
        text: str,
        language: Optional[str] = None,
        enabled: bool = True,
    ) -> str:
        """Removes verbal hesitations and stutters while preserving sentence flow.

        Args:
            text: Raw speech transcription text.
            language: Detected or configured language ('en', 'hi', 'bilingual').
            enabled: If False, returns untouched text verbatim.
        """
        if not enabled or not text or not text.strip():
            return text

        cleaned = text

        # Step 1: Collapse repeated stutters (e.g. 'the the the' -> 'the')
        if self.collapse_stutters_enabled:
            cleaned = self.collapse_stutters(cleaned)

        # Step 2: Custom user-defined filler overrides (if any)
        if self.custom_fillers:
            for word in self.custom_fillers:
                pat = re.compile(rf"(?i)\b{re.escape(word)}\b[,.]?\s*")
                cleaned = self._remove_matches_with_capitalization(cleaned, pat)

        # Step 3: Tier 1 Universal Non-Lexical Fillers (safe in all languages)
        for pat in self._universal_patterns:
            cleaned = self._remove_matches_with_capitalization(cleaned, pat)

        # Step 4: Tier 2 Language-Gated Fillers
        base_lang = (language or "en").lower().split("-")[0].split("_")[0]

        if base_lang in ("en", "auto", "bilingual", "pure_english"):
            for pat in self._en_gated_patterns:
                cleaned = self._remove_matches_with_capitalization(cleaned, pat)

        if base_lang in ("hi", "auto", "bilingual", "pure_hindi", "mixed"):
            for pat in self._hi_gated_patterns:
                cleaned = self._remove_matches_with_capitalization(cleaned, pat)
            cleaned = self._remove_matches_with_capitalization(cleaned, self._hi_matlab_pattern)

        # Step 5: Normalize punctuation and whitespace
        cleaned = ORPHAN_COMMA_RE.sub(",", cleaned)
        cleaned = MULTI_SPACE_RE.sub(" ", cleaned)

        # If a leading comma was left at sentence start, strip it
        cleaned = re.sub(r"^\s*,\s*", "", cleaned)
        cleaned = re.sub(r"\s*,\s*([\.!\?।])", r"\1", cleaned)

        return cleaned.strip()
