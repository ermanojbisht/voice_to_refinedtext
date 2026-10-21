"""Tests for the TTS Text Normalizer & Speech Preprocessor.

Verifies that raw Markdown notes, Obsidian daily notes, checkboxes, emojis,
Indian currency expressions, and technical units are transformed into clean,
natural spoken text for speech synthesizers.
"""
import pytest

from pwd_helper.tts.normalizer import (
    clean_for_speech,
    expand_indian_currency,
    expand_engineering_units,
    detect_speech_language,
    strip_markdown_and_emojis,
)


def test_strip_yaml_frontmatter():
    raw = """---
date: 2026-10-20
tags: [review, pmd]
reviewed: true
---
# Evening Review
Today was a productive day at the Chamba division.
"""
    cleaned = clean_for_speech(raw)
    assert "date: 2026-10-20" not in cleaned
    assert "tags:" not in cleaned
    assert "Evening Review" in cleaned
    assert "Today was a productive day" in cleaned


def test_strip_markdown_formatting():
    raw = """
## Site Inspection
We checked the **foundation** and *pier caps*.
Refer to [Inspection Report](https://pwd.hp.gov.in/rep/101) for details.
> Note: Water level was normal.
`gcc -O3` was not used.
"""
    cleaned = clean_for_speech(raw)
    assert "##" not in cleaned
    assert "**" not in cleaned
    assert "*" not in cleaned
    assert "https://pwd.hp.gov.in" not in cleaned
    assert "Inspection Report" in cleaned
    assert "foundation and pier caps" in cleaned
    assert "Note: Water level was normal." in cleaned
    assert "`" not in cleaned


def test_checkbox_task_transformation():
    raw = """
### Tasks for Tomorrow:
- [ ] Submit Chamba bridge DPR to Superintending Engineer
- [x] Clear measurement book entries for contractor
* [ ] Verify steel batch test certificates
"""
    cleaned = clean_for_speech(raw)
    assert "- [ ]" not in cleaned
    assert "- [x]" not in cleaned
    assert "* [ ]" not in cleaned
    assert "To do: Submit चंबा bridge DPR" in cleaned
    assert "Completed: Clear measurement book entries" in cleaned
    assert "To do: Verify steel batch test certificates" in cleaned


def test_phonetic_indian_names():
    raw = "Good morning Manoj, welcome to Uttarakhand."
    cleaned = clean_for_speech(raw)
    assert "मनोज" in cleaned
    assert "उत्तराखंड" in cleaned


def test_strip_markdown_tables_and_separators():
    raw = """
Summary of works:
| Item | Cost | Status |
| --- | --- | --- |
| Bridge | ₹1.5 lakh | Completed |
| Approach Road | ₹50,000 | Pending |
---
End of report.
"""
    cleaned = clean_for_speech(raw)
    assert "|" not in cleaned
    assert "---" not in cleaned
    assert "Bridge" in cleaned
    assert "End of report" in cleaned


def test_strip_emojis_and_badges():
    raw = "🚨 CRITICAL ALERT: Site inspection completed successfully! ✨ 📋 ✔"
    cleaned = clean_for_speech(raw)
    assert "🚨" not in cleaned
    assert "✨" not in cleaned
    assert "📋" not in cleaned
    assert "✔" not in cleaned
    assert "CRITICAL ALERT: Site inspection completed successfully!" in cleaned


def test_expand_indian_currency_english():
    text = "The estimated budget is ₹500 for materials, ₹1.5 lakh for labour, and ₹2.4 crore for construction."
    expanded = expand_indian_currency(text, lang="en")
    assert "₹" not in expanded
    assert "500 rupees" in expanded
    assert "1.5 lakh rupees" in expanded
    assert "2.4 crore rupees" in expanded


def test_expand_indian_currency_hindi():
    text = "इस काम के लिए ₹500 और ₹2 लाख की आवश्यकता है।"
    expanded = expand_indian_currency(text, lang="hi")
    assert "₹" not in expanded
    assert "500 रुपये" in expanded
    assert "2 लाख रुपये" in expanded


def test_expand_engineering_units():
    text = "Total length is 12.5 km with 50 m3 concrete and 25 mm reinforcement."
    expanded = expand_engineering_units(text)
    assert "12.5 kilometres" in expanded
    assert "50 cubic metres" in expanded
    assert "25 millimetres" in expanded


def test_language_detection():
    assert detect_speech_language("कल साइट पर जाकर निरीक्षण किया था।") == "hi"
    assert detect_speech_language("Today we inspected the Chamba bridge girder alignment.") == "en"
    assert detect_speech_language("आज meeting 10 am ko schedule hui thi.") == "hi"  # Roman Hinglish
