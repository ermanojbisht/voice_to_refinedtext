"""Fuzzy N-Gram Domain Dictionary Engine.

High-performance, in-memory custom word and domain terminology corrector
based on the Handy Rust text.rs architecture.

Key capabilities:
- Multi-token sliding N-gram window (1 to 4 words) to repair split speech tokens
  (e.g., "Chat G P T" -> "ChatGPT", "Charge B" -> "ChargeBee", "Open AI" -> "OpenAI",
   "Mac Book Pro" -> "MacBook Pro", "D P R" -> "DPR", "R and D" -> "R&D").
- Length difference guard (|len_diff| <= max(max_len * 0.25, 2.0)) to prevent
  over-matching short words against long dictionary targets.
- Short-term exact guard: prevents short acronyms (<= 3 chars, e.g. SOR, SDO, EE)
  from accidentally consuming everyday English words (e.g. "for", "site") via
  approximate edit distance; short terms require exact normalized token matches.
- Hybrid distance scoring: Normalized Levenshtein distance combined with
  American Soundex phonetic match boost (70% score discount / 0.3 multiplier).
- Clause-boundary protection: never consumes n-grams across sentence/clause
  punctuation boundaries (commas, periods, semicolons, dashes).
- Preserves boundary punctuation prefix/suffix (e.g. "(Charge B)?" -> "(ChargeBee)?",
  "「Handee。」" -> "「Handy。」").
- Preserves original casing pattern (ALL-CAPS -> ALL-CAPS, Titlecase -> Titlecase).
- Sub-millisecond performance: Pre-computed match keys with exact-match O(1) fast path
  and length-bucketed candidate pruning.
- Zero external dependencies: pure standard library.

Compatible with Python 3.10 through 3.14.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Phonetic & String Distance Algorithms
# ---------------------------------------------------------------------------

_SOUNDEX_MAP = {
    "B": "1", "F": "1", "P": "1", "V": "1",
    "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
    "D": "3", "T": "3",
    "L": "4",
    "M": "5", "N": "5",
    "R": "6",
}


def soundex(text: str) -> str:
    """Computes the 4-character American Soundex code for an ASCII word.

    Format: 1 uppercase letter followed by 3 digits (e.g. 'C621').
    Returns an empty string if text contains no ASCII alphabetic characters.
    """
    if not text:
        return ""
    letters = [c.upper() for c in text if "A" <= c.upper() <= "Z"]
    if not letters:
        return ""

    first_letter = letters[0]
    digits: List[str] = []
    prev_code = _SOUNDEX_MAP.get(first_letter, "0")

    for ch in letters[1:]:
        code = _SOUNDEX_MAP.get(ch, "0")
        if code != "0":
            if code != prev_code:
                digits.append(code)
            prev_code = code
        else:
            if ch not in ("H", "W"):
                prev_code = "0"

    code_str = first_letter + "".join(digits)
    return (code_str + "000")[:4]


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculates Levenshtein edit distance between two strings using 2-row DP."""
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    if len(s1) < len(s2):
        s1, s2 = s2, s1

    # s1 is longer or equal
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1] * (len(s2) + 1)
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (0 if c1 == c2 else 1)
            curr_row[j + 1] = min(insertions, deletions, substitutions)
        prev_row = curr_row

    return prev_row[-1]


# ---------------------------------------------------------------------------
# Key Normalization & Boundary Utilities
# ---------------------------------------------------------------------------

def is_supported_fuzzy_key(key: str) -> bool:
    """Returns True if key is non-empty and contains only ASCII alphanumeric chars."""
    return bool(key) and key.isalnum() and key.isascii()


def supports_soundex(key: str) -> bool:
    """Returns True if key is non-empty and contains only ASCII alphabetic chars."""
    return bool(key) and key.isalpha() and key.isascii()


def build_match_key(word: str) -> str:
    """Builds a normalized lowercase alphanumeric key from a word."""
    return "".join(c.lower() for c in word if c.isalnum())


def build_ngram(words: Sequence[str]) -> str:
    """Strips punctuation from each word, lowercases, and joins without spaces."""
    return "".join(build_match_key(w) for w in words)


def extract_punctuation(word: str) -> Tuple[str, str]:
    """Extracts leading and trailing punctuation from a word.

    Uses character-by-character scan to support multi-byte Unicode punctuation
    (e.g., Japanese brackets, smart quotes, em-dashes) without splitting chars.
    """
    if not word:
        return "", ""

    first_alnum = -1
    for idx, ch in enumerate(word):
        if ch.isalnum():
            first_alnum = idx
            break

    if first_alnum == -1:
        # No alphanumeric characters found; entire word is punctuation
        return word, ""

    last_alnum = first_alnum
    for idx in range(len(word) - 1, -1, -1):
        if word[idx].isalnum():
            last_alnum = idx
            break

    prefix = word[:first_alnum]
    suffix = word[last_alnum + 1:]
    return prefix, suffix


def preserve_case_pattern(original: str, replacement: str) -> str:
    """Preserves the casing pattern of the original word onto the replacement."""
    if not original or not replacement:
        return replacement

    alnum_chars = [c for c in original if c.isalnum()]
    if not alnum_chars:
        return replacement

    if all(c.isupper() for c in alnum_chars):
        return replacement.upper()
    elif alnum_chars[0].isupper():
        return replacement[0].upper() + replacement[1:]
    else:
        return replacement


class CustomWordMatchKey:
    """Pre-computed match key with caching for length and soundex."""
    __slots__ = ("word_index", "key", "length", "soundex")

    def __init__(self, word_index: int, key: str) -> None:
        self.word_index = word_index
        self.key = key
        self.length = len(key)
        self.soundex = soundex(key) if supports_soundex(key) else ""


def build_custom_word_match_keys(word: str, word_index: int) -> List[CustomWordMatchKey]:
    """Pre-computes comparison keys for a custom dictionary word.

    Supports '&' expansion (e.g. 'R&D' generates both 'rd' and 'randd').
    """
    primary_key = build_match_key(word)
    keys: List[CustomWordMatchKey] = []

    if is_supported_fuzzy_key(primary_key):
        keys.append(CustomWordMatchKey(word_index=word_index, key=primary_key))

    if "&" in word:
        expanded_key = build_match_key(word.replace("&", " and "))
        if is_supported_fuzzy_key(expanded_key) and expanded_key != primary_key:
            keys.append(CustomWordMatchKey(word_index=word_index, key=expanded_key))

    return keys


# ---------------------------------------------------------------------------
# Matching Core
# ---------------------------------------------------------------------------

def find_best_match(
    candidate: str,
    custom_words: Sequence[str],
    custom_word_match_keys: Sequence[CustomWordMatchKey],
    threshold: float,
    exact_map: Optional[Dict[str, str]] = None,
    keys_by_len: Optional[Dict[int, List[CustomWordMatchKey]]] = None,
) -> Optional[Tuple[str, float]]:
    """Finds the best matching custom word for a candidate string.

    Uses an O(1) fast-path for exact matches, normalized Levenshtein distance,
    Soundex phonetic matching, length-difference pruning, and short-term safeguards.
    """
    if not is_supported_fuzzy_key(candidate) or len(candidate) > 50:
        return None

    # O(1) exact match fast-path
    if exact_map and candidate in exact_map:
        return exact_map[candidate], 0.0

    candidate_len = len(candidate)

    # Short-term protection: terms under 4 characters (e.g. EE, AE, MB, SOR, SDO)
    # require exact matches to avoid replacing ordinary short words (e.g. 'for', 'site')
    if candidate_len < 4:
        return None

    candidate_soundex = soundex(candidate) if supports_soundex(candidate) else ""

    best_match: Optional[str] = None
    best_score = float("inf")

    # If length-indexed buckets are provided, iterate only over relevant lengths
    if keys_by_len is not None:
        max_diff = int(max(candidate_len * 0.25, 2.0))
        min_l = max(4, candidate_len - max_diff)
        max_l = candidate_len + max_diff
        candidate_keys: List[CustomWordMatchKey] = []
        for l in range(min_l, max_l + 1):
            bucket = keys_by_len.get(l)
            if bucket:
                candidate_keys.extend(bucket)
    else:
        candidate_keys = list(custom_word_match_keys)

    for custom_word_key in candidate_keys:
        custom_word_len = custom_word_key.length

        # Skip short target words under 4 chars unless exact
        if custom_word_len < 4:
            if candidate == custom_word_key.key:
                return custom_words[custom_word_key.word_index], 0.0
            continue

        len_diff = abs(candidate_len - custom_word_len)
        max_len = max(candidate_len, custom_word_len)

        # Length difference guard: reject if length difference exceeds 25% (min 2 chars)
        max_allowed_diff = max(max_len * 0.25, 2.0)
        if len_diff > max_allowed_diff:
            continue

        if candidate == custom_word_key.key:
            return custom_words[custom_word_key.word_index], 0.0

        # Levenshtein distance normalized by maximum string length
        lev_dist = levenshtein_distance(candidate, custom_word_key.key)
        lev_score = (lev_dist / max_len) if max_len > 0 else 1.0

        # Phonetic match boost (Soundex)
        phonetic_match = False
        if candidate_soundex and custom_word_key.soundex:
            if candidate_soundex == custom_word_key.soundex:
                phonetic_match = True

        combined_score = (lev_score * 0.3) if phonetic_match else lev_score

        if combined_score < threshold and combined_score < best_score:
            best_match = custom_words[custom_word_key.word_index]
            best_score = combined_score

    if best_match is not None:
        return best_match, best_score
    return None


def apply_custom_words(
    text: str,
    custom_words: Sequence[str],
    threshold: float = 0.35,
    max_ngram: int = 4,
) -> str:
    """Applies custom word corrections to transcribed text using fuzzy n-gram matching."""
    if not text or not custom_words:
        return text

    # Pre-compute match keys, length buckets, and exact map
    match_keys: List[CustomWordMatchKey] = []
    exact_map: Dict[str, str] = {}
    keys_by_len: Dict[int, List[CustomWordMatchKey]] = {}

    for idx, word in enumerate(custom_words):
        keys = build_custom_word_match_keys(word, idx)
        match_keys.extend(keys)
        for k in keys:
            if k.key not in exact_map:
                exact_map[k.key] = word
            keys_by_len.setdefault(k.length, []).append(k)

    if not match_keys:
        return text

    words = text.split()
    if not words:
        return text

    result: List[str] = []
    i = 0
    num_words = len(words)

    while i < num_words:
        best_match: Optional[Tuple[int, str, float]] = None

        for n in range(min(max_ngram, num_words - i), 0, -1):
            ngram_words = words[i:i + n]

            # Do not cross punctuation boundary
            if any(extract_punctuation(w)[1] for w in ngram_words[:-1]):
                continue

            ngram = build_ngram(ngram_words)
            match_res = find_best_match(
                ngram, custom_words, match_keys, threshold, exact_map, keys_by_len
            )

            if match_res is not None:
                replacement, score = match_res
                # Choose strictly lower score. If scores are tied within 1e-5, prefer
                # fewer tokens (smaller n) to prevent swallowing following words.
                if best_match is None or (score < best_match[2] - 1e-5):
                    best_match = (n, replacement, score)
                elif abs(score - best_match[2]) <= 1e-5 and n < best_match[0]:
                    best_match = (n, replacement, score)

        if best_match is not None:
            n, replacement, _ = best_match
            ngram_words = words[i:i + n]
            prefix, _ = extract_punctuation(ngram_words[0])
            _, suffix = extract_punctuation(ngram_words[-1])
            corrected = preserve_case_pattern(ngram_words[0], replacement)
            result.append(f"{prefix}{corrected}{suffix}")
            i += n
        else:
            result.append(words[i])
            i += 1

    return " ".join(result)


# ---------------------------------------------------------------------------
# High-Level Matcher Class & Dictionary Aggregator
# ---------------------------------------------------------------------------

class FuzzyCustomWordMatcher:
    """In-memory fuzzy custom word matcher with pre-compiled index keys."""

    def __init__(
        self,
        custom_words: Optional[Sequence[str]] = None,
        threshold: float = 0.35,
        max_ngram: int = 4,
    ) -> None:
        self.threshold = threshold
        self.max_ngram = max_ngram
        self._custom_words: List[str] = []
        self._match_keys: List[CustomWordMatchKey] = []
        self._exact_map: Dict[str, str] = {}
        self._keys_by_len: Dict[int, List[CustomWordMatchKey]] = {}
        if custom_words:
            self.set_custom_words(custom_words)

    def set_custom_words(self, words: Sequence[str]) -> None:
        """Indexes a new list of custom words for high-speed matching."""
        seen = set()
        deduped: List[str] = []
        for w in words:
            w_str = str(w).strip()
            if w_str and w_str not in seen:
                seen.add(w_str)
                deduped.append(w_str)

        self._custom_words = deduped
        keys: List[CustomWordMatchKey] = []
        exact_map: Dict[str, str] = {}
        keys_by_len: Dict[int, List[CustomWordMatchKey]] = {}

        for idx, word in enumerate(self._custom_words):
            word_keys = build_custom_word_match_keys(word, idx)
            keys.extend(word_keys)
            for k in word_keys:
                if k.key not in exact_map:
                    exact_map[k.key] = word
                keys_by_len.setdefault(k.length, []).append(k)

        self._match_keys = keys
        self._exact_map = exact_map
        self._keys_by_len = keys_by_len

    def apply(self, text: str, threshold: Optional[float] = None) -> str:
        """Applies custom word corrections using the pre-compiled match keys."""
        if not text or not self._custom_words or not self._match_keys:
            return text

        active_thresh = self.threshold if threshold is None else threshold
        words = text.split()
        if not words:
            return text

        result: List[str] = []
        i = 0
        num_words = len(words)

        while i < num_words:
            best_match: Optional[Tuple[int, str, float]] = None

            for n in range(min(self.max_ngram, num_words - i), 0, -1):
                ngram_words = words[i:i + n]

                if any(extract_punctuation(w)[1] for w in ngram_words[:-1]):
                    continue

                ngram = build_ngram(ngram_words)
                match_res = find_best_match(
                    ngram,
                    self._custom_words,
                    self._match_keys,
                    active_thresh,
                    self._exact_map,
                    self._keys_by_len,
                )

                if match_res is not None:
                    replacement, score = match_res
                    if best_match is None or (score < best_match[2] - 1e-5):
                        best_match = (n, replacement, score)
                    elif abs(score - best_match[2]) <= 1e-5 and n < best_match[0]:
                        best_match = (n, replacement, score)

            if best_match is not None:
                n, replacement, _ = best_match
                ngram_words = words[i:i + n]
                prefix, _ = extract_punctuation(ngram_words[0])
                _, suffix = extract_punctuation(ngram_words[-1])
                corrected = preserve_case_pattern(ngram_words[0], replacement)
                result.append(f"{prefix}{corrected}{suffix}")
                i += n
            else:
                result.append(words[i])
                i += 1

        return " ".join(result)


def load_all_domain_words(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Loads all domain words from config.json, pwd_dict.json, and pwd_custom_dict.json.

    Returns:
        Consolidated list of unique custom words ready for indexing.
    """
    words: List[str] = []

    # 1. Config custom words
    if config:
        cfg_custom = config.get("CUSTOM_WORDS", [])
        if isinstance(cfg_custom, list):
            words.extend(str(w) for w in cfg_custom if w)

    # 2. PWD Core Dictionary
    try:
        from pwd_helper.core import get_pwd_dict
        pwd_dict = get_pwd_dict()
        for abbr in pwd_dict.keys():
            words.append(abbr)
    except Exception:
        pass

    # 3. Common domain multi-word engineering phrases
    domain_phrases = [
        "culvert widening",
        "earthwork",
        "ChatGPT",
        "OpenAI",
        "Claude",
        "MacBook Pro",
        "ChargeBee",
        "GitHub",
        "DevOps",
    ]
    words.extend(domain_phrases)

    # De-duplicate while preserving order
    seen = set()
    result = []
    for w in words:
        clean = w.strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)

    return result
