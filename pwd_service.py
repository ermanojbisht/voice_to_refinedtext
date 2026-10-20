"""Backend service for PWD Terminology & SOR Glossary web explorer.

Provides categorized lookup, search, custom abbreviation management,
and bilingual terminology normalization for web clients.
"""
from __future__ import annotations

import os
import re
import sys
from typing import Dict, Any, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import pwd_helper
from pwd_helper.core import (
    get_pwd_dict,
    lookup_abbreviation,
    search_abbreviations,
    add_custom_abbreviation,
    list_by_category,
)
from pwd_helper.normalizer import normalize_pwd_terms
from pwd_helper.translator import process_input, translate


def parse_meaning(raw_meaning: str) -> Dict[str, str]:
    """Splits 'English Full Name (Hindi Name)' into clean components."""
    match = re.match(r"^(.*?)\s*\((.*?)\)\s*$", raw_meaning.strip())
    if match:
        return {
            "english": match.group(1).strip(),
            "hindi": match.group(2).strip(),
            "full": raw_meaning.strip(),
        }
    return {
        "english": raw_meaning.strip(),
        "hindi": "",
        "full": raw_meaning.strip(),
    }


def get_all_terms() -> Dict[str, Any]:
    """Returns all standard and custom PWD abbreviations with parsed bilingual names."""
    d = get_pwd_dict(reload=True)
    terms = []
    categories = set()

    for abbr, info in sorted(d.items()):
        parsed = parse_meaning(info["meaning"])
        cat = info.get("category", "general")
        categories.add(cat)
        terms.append({
            "abbr": abbr,
            "category": cat,
            "english": parsed["english"],
            "hindi": parsed["hindi"],
            "full": parsed["full"],
        })

    return {
        "total": len(terms),
        "categories": sorted(list(categories)),
        "terms": terms,
    }


def search_terms(query: str) -> List[Dict[str, Any]]:
    """Fuzzy searches abbreviations, English full forms, and Hindi names."""
    if not query or not query.strip():
        return get_all_terms()["terms"]

    results = search_abbreviations(query.strip())
    terms = []
    for abbr, info in sorted(results.items()):
        parsed = parse_meaning(info["meaning"])
        terms.append({
            "abbr": abbr,
            "category": info.get("category", "general"),
            "english": parsed["english"],
            "hindi": parsed["hindi"],
            "full": parsed["full"],
        })
    return terms


def add_custom_term(abbr: str, english: str, hindi: str = "", category: str = "custom") -> Dict[str, Any]:
    """Adds a new custom term and saves to custom dictionary."""
    if not abbr.strip() or not english.strip():
        return {"ok": False, "error": "Abbreviation and English meaning are required."}

    full_meaning = f"{english.strip()} ({hindi.strip()})" if hindi.strip() else english.strip()
    success = add_custom_abbreviation(abbr.strip(), full_meaning, category=category or "custom")
    return {"ok": success, "abbr": abbr.strip().upper(), "meaning": full_meaning}


def translate_sandbox(text: str, mode: str = "auto", expand: bool = True) -> Dict[str, Any]:
    """Normalizes abbreviations and provides bilingual translation."""
    if not text or not text.strip():
        return {"normalized": "", "translation": "", "method": "none"}

    normalized = normalize_pwd_terms(text.strip(), expand=expand)
    res = process_input(normalized, mode=mode)
    return {
        "original": text,
        "normalized": normalized,
        "translation": res.get("translation", res.get("meaning", "")),
        "method": res.get("method", res.get("type", "abbreviation")),
    }


class PWDService:
    """Class interface and singleton manager for PWD terminology services."""
    _instance: Optional["PWDService"] = None

    @classmethod
    def get_instance(cls) -> "PWDService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_terms(self) -> List[Dict[str, Any]]:
        return get_all_terms()["terms"]

    def get_categories(self) -> List[str]:
        return get_all_terms()["categories"]

    def search(self, query: str, category: str = "All") -> List[Dict[str, Any]]:
        results = search_terms(query)
        if category and category != "All":
            results = [r for r in results if r.get("category", "").lower() == category.lower()]
        return results

    def add_custom_term(self, abbr: str, english: str, hindi: str = "", category: str = "Custom") -> Dict[str, Any]:
        res = add_custom_term(abbr, english, hindi, category)
        return {
            "term": res.get("abbr", abbr),
            "meaning_en": english,
            "meaning_hi": hindi,
            "category": category,
            "ok": res.get("ok", False)
        }

    def translate_text(self, text: str, mode: str = "auto") -> Dict[str, Any]:
        res = translate_sandbox(text, mode=mode)
        return {
            "original": res["original"],
            "en": res["normalized"],
            "hi": res["translation"],
            "method": res["method"]
        }

