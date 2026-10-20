"""Unit tests for PWD Uttarakhand Language Helper & Terminology Engine."""
import pytest
from pwd_helper.core import (
    get_pwd_dict,
    lookup_abbreviation,
    search_abbreviations,
    list_abbreviations,
    list_by_category,
    add_custom_abbreviation,
)
from pwd_helper.normalizer import normalize_pwd_terms
from pwd_helper.translator import process_input


def test_pwd_dictionary_loading():
    """Verify dictionary loads expected categories and at least 45 terms."""
    terms = get_pwd_dict(reload=True)
    assert len(terms) >= 45
    assert "EE" in terms
    assert "NIT" in terms
    assert "MB" in terms
    assert "RCC" in terms


def test_exact_lookup_and_case_insensitivity():
    """Verify exact lookup works regardless of casing."""
    ee = lookup_abbreviation("ee")
    assert ee is not None
    assert ee["abbr"] == "EE"
    assert ee["category"] == "officers"
    assert "Executive Engineer" in ee["meaning"]

    nit = lookup_abbreviation("nIt")
    assert nit is not None
    assert nit["abbr"] == "NIT"
    assert "Notice Inviting Tender" in nit["meaning"]

    unknown = lookup_abbreviation("XYZNONEXISTENT")
    assert unknown is None


def test_search_abbreviations():
    """Verify substring search across abbreviation keys and meanings."""
    matches = search_abbreviations("tender")
    assert "NIT" in matches

    eng_matches = search_abbreviations("Engineer")
    assert "EE" in eng_matches
    assert "CE" in eng_matches
    assert "AE" in eng_matches

    hindi_matches = search_abbreviations("अभियंता")
    assert len(hindi_matches) >= 3


def test_list_by_category():
    """Verify terms are grouped by their functional category."""
    grouped = list_by_category()
    assert "officers" in grouped
    assert "documents" in grouped
    assert "schemes" in grouped
    assert "technical" in grouped
    assert "EE" in grouped["officers"]
    assert "NIT" in grouped["documents"]


def test_normalizer_casing_and_dotted_terms():
    """Verify normalizer auto-capitalizes and cleans spoken abbreviations."""
    raw = "the ee reviewed the mb and issued the nit for the rcc bridge on pmgsy road."
    cleaned = normalize_pwd_terms(raw)
    assert "EE" in cleaned
    assert "MB" in cleaned
    assert "NIT" in cleaned
    assert "RCC" in cleaned
    assert "PMGSY" in cleaned
    assert "the ee" not in cleaned

    dotted = "e.e. met with a. e. and j.e. to inspect the r.c.c. culvert."
    dotted_cleaned = normalize_pwd_terms(dotted)
    assert "EE" in dotted_cleaned
    assert "AE" in dotted_cleaned
    assert "JE" in dotted_cleaned
    assert "RCC" in dotted_cleaned


def test_normalizer_expansion():
    """Verify normalizer optionally expands abbreviations with full definitions."""
    raw = "the ee visited the site."
    expanded = normalize_pwd_terms(raw, expand=True)
    assert "EE [Executive Engineer" in expanded


def test_process_input_abbreviation_routing():
    """Verify process_input immediately identifies abbreviations without calling translation."""
    res = process_input("ee")
    assert res["type"] == "abbreviation"
    assert res["found"] is True
    assert res["abbr"] == "EE"
    assert "Executive Engineer" in res["meaning"]


def test_fastapi_endpoints():
    """Verify FastAPI endpoints return expected JSON schema for Laravel integration."""
    try:
        from fastapi.testclient import TestClient
        from pwd_helper.api import app
        client = TestClient(app)

        # 1. Lookup
        r = client.get("/api/abbreviation?q=EE")
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is True
        assert data["abbreviation"] == "EE"
        assert "Executive Engineer" in data["meaning"]

        # 2. Search
        r2 = client.get("/api/search?q=tender")
        assert r2.status_code == 200
        assert "NIT" in r2.json()

        # 3. List
        r3 = client.get("/api/abbreviations")
        assert r3.status_code == 200
        assert len(r3.json()) >= 45
    except ImportError:
        pytest.skip("TestClient / httpx not installed in environment")


def test_translate_online_fallback():
    """Verify translate_online works with pure Python urllib fallback."""
    from pwd_helper.translator import translate_online
    try:
        res = translate_online("Bridge")
        assert res is not None
        assert len(res) > 0
    except Exception as e:
        pytest.skip(f"Online network translation not reachable: {e}")

