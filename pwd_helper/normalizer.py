"""Speech transcript normalizer for PWD Uttarakhand engineering terminology.

Automatically detects and corrects PWD abbreviations in Whisper / Nemotron speech
transcripts, ensuring accurate uppercase casing and optional definition expansions.
Compatible with Python 3.10 through 3.14.
"""
from __future__ import annotations

import re
from typing import Dict, Pattern
from pwd_helper.core import get_pwd_dict

# Common dotted spoken patterns mapped to canonical abbreviations
DOTTED_MAP: Dict[str, str] = {
    r"\be[\.\s]+e\b": "EE",
    r"\ba[\.\s]+e\b": "AE",
    r"\bj[\.\s]+e\b": "JE",
    r"\bs[\.\s]+e\b": "SE",
    r"\bc[\.\s]+e\b": "CE",
    r"\bm[\.\s]+b\b": "MB",
    r"\bn[\.\s]+i[\.\s]+t\b": "NIT",
    r"\bs[\.\s]+o[\.\s]+r\b": "SOR",
    r"\bb[\.\s]+o[\.\s]+q\b": "BOQ",
    r"\bd[\.\s]+p[\.\s]+r\b": "DPR",
    r"\br[\.\s]+c[\.\s]+c\b": "RCC",
    r"\bp[\.\s]+c[\.\s]+c\b": "PCC",
    r"\bw[\.\s]+b[\.\s]+m\b": "WBM",
    r"\bg[\.\s]+s[\.\s]+b\b": "GSB",
    r"\bd[\.\s]+b[\.\s]+m\b": "DBM",
    r"\bp[\.\s]+m[\.\s]+g[\.\s]+s[\.\s]+y\b": "PMGSY",
    r"\be[\.\s]+i[\.\s]+n[\.\s]+c\b": "E-IN-C",
    r"\bmanuble\b": "manual",
    r"\be\s+and\s+je\b": "EE and JE",
    r"\btfo\s+office\b": "DFO office",
    r"\bculvert\s+(?:white\s+ink|winding|wiring)\b": "culvert widening",
    r"\bconvert\s+wiring\b": "culvert widening",
    r"\barthe?work\b": "earthwork",
    r"\bartha?\s+work\b": "earthwork",
    r"\bartha?\s+quantity\b": "earthwork quantity",
    r"\bartha?bhar\b": "earthwork",
}

_DOTTED_COMPILED: list[tuple[Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), repl) for pattern, repl in DOTTED_MAP.items()
]


def normalize_pwd_terms(text: str, expand: bool = False) -> str:
    """Corrects PWD abbreviation casing and terminology in spoken text.

    Args:
        text: Raw transcription text from speech recognition.
        expand: If True, appends the official English designation and Hindi meaning
                in brackets after the abbreviation on its first occurrence.

    Returns:
        Normalized text with canonical PWD engineering terms.
    """
    if not text:
        return ""

    normalized = text

    # 1. Normalize dotted and spaced acronyms (e.g. 'e.e.', 'm. b.', 'r.c.c.')
    for pattern, repl in _DOTTED_COMPILED:
        normalized = pattern.sub(repl, normalized)

    # 2. Case-correct exact abbreviation word matches
    terms = get_pwd_dict()
    expanded_set: set[str] = set()

    # Sort keys by descending length so multi-word or longer terms match first
    sorted_abbrs = sorted(terms.keys(), key=lambda k: len(k), reverse=True)

    for abbr in sorted_abbrs:
        # Match whole word boundaries case-insensitively
        # Handle hyphenated abbreviations like E-IN-C or RA BILL
        escaped = re.escape(abbr)
        pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)

        if not pattern.search(normalized):
            continue

        if expand and abbr not in expanded_set:
            info = terms[abbr]
            meaning = info.get("meaning", "")
            replacement = f"{abbr} [{meaning}]" if meaning else abbr
            # Replace only the first occurrence with expansion, remaining with uppercase abbr
            normalized = pattern.sub(replacement, normalized, count=1)
            expanded_set.add(abbr)
            normalized = pattern.sub(abbr, normalized)
        else:
            normalized = pattern.sub(abbr, normalized)

    return normalized
