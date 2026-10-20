"""Core logic for PWD Uttarakhand terminology lookup and management.

Loads standard PWD Uttarakhand abbreviations and user-defined custom extensions.
Compatible with Python 3.10 through 3.14.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_FILE = os.path.join(SCRIPT_DIR, "pwd_dict.json")
CUSTOM_DICT_FILE = os.path.join(SCRIPT_DIR, "pwd_custom_dict.json")

_pwd_dict: Optional[Dict[str, Dict[str, str]]] = None


def get_pwd_dict(reload: bool = False) -> Dict[str, Dict[str, str]]:
    """Load and merge standard and custom PWD abbreviation dictionaries.

    Returns:
        Dict mapping uppercase abbreviation to a dict with 'category', 'meaning', and 'abbr'.
    """
    global _pwd_dict
    if _pwd_dict is not None and not reload:
        return _pwd_dict

    merged: Dict[str, Dict[str, str]] = {}

    # Load base dictionary
    if os.path.exists(DICT_FILE):
        try:
            with open(DICT_FILE, "r", encoding="utf-8") as f:
                base_data = json.load(f)
            for category, terms in base_data.items():
                if isinstance(terms, dict):
                    for abbr, meaning in terms.items():
                        merged[abbr.upper().strip()] = {
                            "abbr": abbr.strip(),
                            "category": category,
                            "meaning": str(meaning),
                        }
        except Exception:
            pass

    # Merge custom user extensions if present
    if os.path.exists(CUSTOM_DICT_FILE):
        try:
            with open(CUSTOM_DICT_FILE, "r", encoding="utf-8") as f:
                custom_data = json.load(f)
            for category, terms in custom_data.items():
                if isinstance(terms, dict):
                    for abbr, meaning in terms.items():
                        merged[abbr.upper().strip()] = {
                            "abbr": abbr.strip(),
                            "category": category,
                            "meaning": str(meaning),
                        }
        except Exception:
            pass

    _pwd_dict = merged
    return _pwd_dict


def lookup_abbreviation(text: str) -> Optional[Dict[str, str]]:
    """Exact case-insensitive match lookup for a PWD abbreviation.

    Args:
        text: Abbreviation text to lookup (e.g. 'EE', 'ee', 'NIT').

    Returns:
        Dictionary with 'abbr', 'category', and 'meaning', or None if not found.
    """
    if not text:
        return None
    d = get_pwd_dict()
    key = text.upper().strip()
    return d.get(key)


def search_abbreviations(query: str) -> Dict[str, Dict[str, str]]:
    """Partial match search across abbreviations and their meanings.

    Args:
        query: Search term in English or Hindi (e.g. 'Engineer', 'अभियंता', 'tender').

    Returns:
        Dictionary of matching abbreviations.
    """
    if not query or not query.strip():
        return {}
    d = get_pwd_dict()
    q = query.strip().lower()
    return {
        k: v for k, v in d.items()
        if q in k.lower() or q in v["meaning"].lower() or q in v["category"].lower()
    }


def list_abbreviations() -> Dict[str, Dict[str, str]]:
    """Return all available PWD abbreviations."""
    return get_pwd_dict()


def list_by_category() -> Dict[str, Dict[str, str]]:
    """Return abbreviations grouped by their functional category."""
    d = get_pwd_dict()
    grouped: Dict[str, Dict[str, str]] = {}
    for key, info in sorted(d.items()):
        cat = info.get("category", "other")
        if cat not in grouped:
            grouped[cat] = {}
        grouped[cat][key] = info.get("meaning", "")
    return grouped


def add_custom_abbreviation(abbr: str, meaning: str, category: str = "custom") -> bool:
    """Persist a new abbreviation into the custom user dictionary.

    Args:
        abbr: Abbreviation (e.g. 'PMU').
        meaning: Full name and Hindi description.
        category: Functional category (default: 'custom').

    Returns:
        True if persisted successfully.
    """
    abbr_clean = abbr.strip().upper()
    if not abbr_clean or not meaning.strip():
        return False

    custom_data: Dict[str, Dict[str, str]] = {}
    if os.path.exists(CUSTOM_DICT_FILE):
        try:
            with open(CUSTOM_DICT_FILE, "r", encoding="utf-8") as f:
                custom_data = json.load(f)
        except Exception:
            custom_data = {}

    if category not in custom_data:
        custom_data[category] = {}
    custom_data[category][abbr_clean] = meaning.strip()

    try:
        with open(CUSTOM_DICT_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_data, f, indent=2, ensure_ascii=False)
        get_pwd_dict(reload=True)
        return True
    except Exception:
        return False
