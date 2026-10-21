"""TTS Text Normalizer and Markdown Preprocessor.

Transforms raw Markdown notes, Obsidian daily documents, checkbox task lists,
emojis, Indian currency markers, and engineering units into clean, phonetically
friendly text for speech synthesizers.
"""
from __future__ import annotations

import re
import unicodedata

# Unicode Emoji & Pictograph regex range
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended
    "\U00002600-\U000026FF"  # misc symbols
    "\U00002B50-\U00002B55"
    "\U0000200D"              # zero-width joiner
    "\U0000FE0F"              # variation selector-16
    "\u2714\u2713\u2716\u2715\u2705"  # checkmarks & crosses
    "]+",
    flags=re.UNICODE,
)

# Common Roman Hinglish marker tokens (excluding ambiguous common English words like 'the')
_HINGLISH_MARKERS = {
    "hai", "hain", "tha", "thi", "karna", "karo", "kare", "karenge",
    "hua", "hue", "hui", "hoga", "hogi", "ka", "ki", "ke", "ko", "se", "mein",
    "par", "aur", "ya", "nahi", "aaj", "kal", "abhi", "baad", "raha", "rahi",
    "rahe", "yeh", "voh", "kya", "kyun", "kaise", "apna", "apni", "apne"
}


def detect_speech_language(text: str) -> str:
    """Classify text as 'hi' (Devanagari / Roman Hinglish) or 'en' (English)."""
    if not text:
        return "en"

    # Count Devanagari and Latin letters
    devanagari_count = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
    latin_count = sum(1 for ch in text if ("a" <= ch.lower() <= "z"))

    # If text is predominantly Devanagari, it is definitely Hindi
    if devanagari_count > 0 and devanagari_count >= latin_count:
        return "hi"

    # Check for Roman-script Hinglish markers
    words = [re.sub(r"[^\w]", "", w.lower()) for w in text.split()]
    hinglish_matches = sum(1 for w in words if w in _HINGLISH_MARKERS)
    if hinglish_matches >= 2 or (len(words) <= 5 and hinglish_matches >= 1 and devanagari_count > 0):
        return "hi"

    return "en"


def strip_yaml_frontmatter(text: str) -> str:
    """Strip Obsidian/Jekyll YAML frontmatter enclosed in leading --- blocks."""
    pattern = r"^---\s*\n.*?\n---\s*\n"
    return re.sub(pattern, "", text, flags=re.DOTALL)


def strip_markdown_and_emojis(text: str) -> str:
    """Strip Markdown syntax, code blocks, links, tables, and visual emojis."""
    if not text:
        return ""

    # Strip YAML frontmatter
    text = strip_yaml_frontmatter(text)

    # Convert checkboxes to speakable task cues
    text = re.sub(r"^[ \t]*[-*]\s*\[\s*\]\s*", "To do: ", text, flags=re.MULTILINE)
    text = re.sub(r"^[ \t]*[-*]\s*\[[xX]\]\s*", "Completed: ", text, flags=re.MULTILINE)

    # Strip code fences and inline code
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Convert Markdown links [label](url) -> label
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Strip Markdown images ![alt](url)
    text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)

    # Strip Markdown headers (#, ##, etc.)
    text = re.sub(r"^[ \t]*#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Strip blockquotes (> )
    text = re.sub(r"^[ \t]*>\s*", "", text, flags=re.MULTILINE)

    # Strip horizontal rules (---, ___, ***)
    text = re.sub(r"^[ \t]*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Clean markdown tables: remove table separator lines | --- | --- |
    text = re.sub(r"^[ \t]*\|[\s\-:|]+\|[ \t]*$", "", text, flags=re.MULTILINE)
    # Remove remaining table pipe delimiters
    text = re.sub(r"\|", " ", text)

    # Strip bold and italics (**word**, *word*, __word__, _word_)
    text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^\*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", text)

    # Strip emojis and pictographs
    text = _EMOJI_PATTERN.sub("", text)

    # Normalize whitespace
    lines = [line.strip() for line in text.splitlines()]
    text = " ".join(line for line in lines if line)
    return re.sub(r"\s+", " ", text).strip()


def expand_indian_currency(text: str, lang: str = "en") -> str:
    """Expand ₹ currency markers into natural words based on language.

    Examples:
      - ₹500 (en) -> 500 rupees
      - ₹1.5 lakh (en) -> 1.5 lakh rupees
      - ₹500 (hi) -> 500 रुपये
      - ₹2 लाख (hi) -> 2 लाख रुपये
    """
    if "₹" not in text:
        return text

    is_hindi = (lang == "hi") or any("\u0900" <= ch <= "\u097F" for ch in text)

    def _replace_currency(match: re.Match) -> str:
        amount = match.group(1).strip()
        unit = match.group(2)
        if unit:
            unit_str = unit.strip()
            if is_hindi:
                return f"{amount} {unit_str} रुपये"
            return f"{amount} {unit_str} rupees"
        else:
            if is_hindi:
                return f"{amount} रुपये"
            return f"{amount} rupees"

    # Pattern matches ₹500, ₹ 1.5 lakh, ₹2.4 crore, ₹ 50,000, ₹2 लाख
    pattern = re.compile(r"₹\s*([0-9,.]+)\s*(lakh|crore|thousand|लाख|करोड़|हज़ार)?", flags=re.IGNORECASE)
    return pattern.sub(_replace_currency, text)


def expand_engineering_units(text: str) -> str:
    """Expand civil engineering abbreviations into phonetically clear words."""
    replacements = [
        (r"\b([0-9.]+)\s*km\b", r"\1 kilometres"),
        (r"\b([0-9.]+)\s*m3\b", r"\1 cubic metres"),
        (r"\b([0-9.]+)\s*mm\b", r"\1 millimetres"),
        (r"\b([0-9.]+)\s*MT\b", r"\1 metric tonnes"),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


_INDIAN_PHONETIC_REPLACEMENTS = [
    (r"\bManoj\b", "मनोज"),
    (r"\bmanoj\b", "मनोज"),
    (r"\bMANOJ\b", "मनोज"),
    (r"\bUttarakhand\b", "उत्तराखंड"),
    (r"\buttarakhand\b", "उत्तराखंड"),
    (r"\bChamba\b", "चंबा"),
    (r"\bchamba\b", "चंबा"),
    (r"\bDehradun\b", "देहरादून"),
    (r"\bdehradun\b", "देहरादून"),
]


def phonetic_indian_names(text: str) -> str:
    """Map Indian names and geographic entities to Devanagari for native phonetic pronunciation."""
    for pattern, replacement in _INDIAN_PHONETIC_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    return text


def clean_for_speech(text: str, lang: str = "auto") -> str:
    """Master pipeline: transforms raw Markdown text into clean, speakable prose."""
    if not text:
        return ""

    if lang == "auto":
        resolved_lang = detect_speech_language(text)
    else:
        resolved_lang = lang

    text = strip_markdown_and_emojis(text)
    text = expand_indian_currency(text, lang=resolved_lang)
    text = expand_engineering_units(text)
    text = phonetic_indian_names(text)

    # Clean double spaces and edge punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text
