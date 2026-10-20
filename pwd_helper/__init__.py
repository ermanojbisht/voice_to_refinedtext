"""PWD Uttarakhand Language Helper & Terminology Engine."""
from __future__ import annotations

from pwd_helper.core import (
    get_pwd_dict,
    lookup_abbreviation,
    search_abbreviations,
    list_abbreviations,
    list_by_category,
    add_custom_abbreviation,
)
from pwd_helper.normalizer import normalize_pwd_terms
from pwd_helper.translator import translate, process_input

__all__ = [
    "get_pwd_dict",
    "lookup_abbreviation",
    "search_abbreviations",
    "list_abbreviations",
    "list_by_category",
    "add_custom_abbreviation",
    "normalize_pwd_terms",
    "translate",
    "process_input",
]
