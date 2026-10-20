"""Tri-tier hybrid translation provider for PWD Uttarakhand notes.

Tiers:
  1. Offline Argos Translate (CTranslate2, fast CPU inference, < 50ms)
  2. Local Ollama LLM (context-aware bilingual refinement)
  3. Online Google Translate (via deep-translator fallback)
Compatible with Python 3.10 through 3.14.
"""
from __future__ import annotations

import warnings
import logging
from typing import Dict, Any, Optional

from pwd_helper.core import lookup_abbreviation

# Suppress noisy library warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.*")
logging.getLogger("stanza").setLevel(logging.ERROR)
logging.getLogger("argostranslate").setLevel(logging.ERROR)

_argos_translator = None


def _get_argos_translator():
    """Lazily load the offline Argos translator package if installed."""
    global _argos_translator
    if _argos_translator is not None:
        return _argos_translator

    try:
        import argostranslate.translate
        installed = argostranslate.translate.get_installed_languages()
        en = next((l for l in installed if l.code == "en"), None)
        hi = next((l for l in installed if l.code == "hi"), None)
        if en and hi:
            _argos_translator = en.get_translation(hi)
            return _argos_translator
    except Exception:
        pass
    return None


def translate_offline(text: str) -> str:
    """Translate using local argos-translate model (CTranslate2)."""
    translator = _get_argos_translator()
    if translator is None:
        raise RuntimeError("Argos offline translation package is not installed.")
    return translator.translate(text)


def translate_online(text: str) -> str:
    """Translate using Google Translate without requiring external third-party packages."""
    # 1. Pure Python urllib request (zero external pip dependencies)
    try:
        import urllib.request
        import urllib.parse
        import json
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=hi&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = "".join(x[0] for x in data[0] if x and len(x) > 0 and x[0]).strip()
            if result:
                return result
    except Exception:
        pass

    # 2. Optional deep_translator fallback if installed
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target="hi").translate(text).strip()
    except Exception as e:
        raise RuntimeError(f"Online translation failed: {e}")


def translate_ollama(text: str, host: str = "", model: str = "") -> str:
    """Translate using local Ollama model."""
    try:
        import utils
        import os
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg = utils.load_config(repo_dir) if repo_dir else {}
        ollama_host = host or cfg.get("OLLAMA_HOST", "http://localhost:11434")
        trans_model = model or cfg.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_hi") or cfg.get("OLLAMA_MODELS", {}).get("hi", "qwen2.5:3b")
        prompt = (
            "Translate the following English construction/official text accurately into natural Hindi. "
            "Output only the Hindi translation, nothing else:\n\n"
            f"{text}"
        )
        res = utils.call_ollama(ollama_host, trans_model, prompt, stop_tokens=[], temperature=0.0, timeout=15)
        if isinstance(res, dict):
            if "error" in res:
                raise RuntimeError(res["error"])
            cleaned = utils.clean_response(res.get("response", ""))
            return cleaned.strip()
        return str(res).strip()
    except Exception as e:
        raise RuntimeError(f"Ollama translation failed: {e}")


def translate(text: str, mode: str = "auto") -> Dict[str, str]:
    """Translate English text to Hindi using the configured strategy.

    Args:
        text: English input text.
        mode: 'offline', 'online', or 'auto' (tries fast offline first, then Ollama, then online).

    Returns:
        Dict with 'translation' and 'method' ('offline_argos', 'ollama', 'online_google').
    """
    cleaned = text.strip()
    if not cleaned:
        return {"translation": "", "method": "none"}

    if mode == "offline":
        try:
            return {"translation": translate_offline(cleaned), "method": "offline_argos"}
        except Exception:
            return {"translation": translate_ollama(cleaned), "method": "ollama"}

    if mode == "online":
        try:
            return {"translation": translate_online(cleaned), "method": "online_google"}
        except Exception:
            return {"translation": translate_ollama(cleaned), "method": "ollama"}

    # Auto mode:
    # 1. Try fast local Argos for short queries if available
    try:
        res = translate_offline(cleaned)
        return {"translation": res, "method": "offline_argos"}
    except Exception:
        pass

    # 2. Try local Ollama
    try:
        res = translate_ollama(cleaned)
        if res:
            return {"translation": res, "method": "ollama"}
    except Exception:
        pass

    # 3. Fallback to Google online
    try:
        res = translate_online(cleaned)
        return {"translation": res, "method": "online_google"}
    except Exception as e:
        raise RuntimeError(f"All translation methods failed: {e}")


def process_input(text: str, mode: str = "auto") -> Dict[str, Any]:
    """Unified entry point matching my_lang_helper contract.

    Checks for exact PWD abbreviation first; if not matched, translates to Hindi.
    """
    abbr = lookup_abbreviation(text)
    if abbr:
        return {
            "type": "abbreviation",
            "input": text.upper().strip(),
            "found": True,
            **abbr,
        }

    res = translate(text, mode)
    return {
        "type": "translation",
        "input": text,
        **res,
    }
