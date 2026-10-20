#!/usr/bin/env python3
"""PWD Uttarakhand — Hybrid Language Helper & Terminology CLI.

Supports both direct one-shot terminal lookups and an interactive REPL with voice dictation.
Compatible with Python 3.10 through 3.14.
"""
from __future__ import annotations

import sys
import os
import argparse
import subprocess

# Ensure project root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from pwd_helper.core import (
    lookup_abbreviation,
    search_abbreviations,
    list_abbreviations,
    list_by_category,
    add_custom_abbreviation,
)
from pwd_helper.translator import process_input, translate
from pwd_helper.normalizer import normalize_pwd_terms


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard via xclip if available."""
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode("utf-8"),
            check=True,
            timeout=2,
        )
        return True
    except Exception:
        return False


def run_one_shot(query: str, mode: str = "auto", copy: bool = False, expand: bool = False):
    """Executes a one-shot query from terminal arguments."""
    query_clean = query.strip()
    if not query_clean:
        return

    # Check for direct commands
    lower = query_clean.lower()
    if lower == "list":
        grouped = list_by_category()
        for cat, terms in sorted(grouped.items()):
            print(f"\n📂 [{cat.upper()}]:")
            for abbr, meaning in sorted(terms.items()):
                print(f"  • {abbr} = {meaning}")
        return

    if lower.startswith("search "):
        term = query_clean.split(None, 1)[1]
        matches = search_abbreviations(term)
        if not matches:
            print(f"No PWD abbreviations found matching '{term}'")
        else:
            print(f"Found {len(matches)} matching abbreviation(s):")
            for abbr, info in sorted(matches.items()):
                print(f"  [{info['category']}] {abbr} = {info['meaning']}")
        return

    if lower.startswith("translate "):
        text_to_trans = query_clean.split(None, 1)[1]
        res = translate(text_to_trans, mode=mode)
        out = f"Hindi ({res['method']}): {res['translation']}"
        print(out)
        if copy:
            copy_to_clipboard(res["translation"])
            print("  (Copied translation to clipboard)")
        return

    # Normal process (Abbreviation check -> Translation)
    res = process_input(query_clean, mode=mode)
    if res["type"] == "abbreviation":
        out = f"[{res['category']}] {res['input']} = {res['meaning']}"
        print(out)
        if copy:
            copy_to_clipboard(f"{res['input']} — {res['meaning']}")
            print("  (Copied abbreviation meaning to clipboard)")
    else:
        out = f"Hindi ({res['method']}): {res['translation']}"
        print(out)
        if copy:
            copy_to_clipboard(res["translation"])
            print("  (Copied translation to clipboard)")


def run_voice_input(mode: str = "auto", copy: bool = True):
    """Captures microphone speech, transcribes, and runs PWD lookup/translation."""
    print("🎙 Initializing microphone...")
    try:
        from engine import VoiceEngine
        engine = VoiceEngine(SCRIPT_DIR)
        print("🎙 Listening... Speak naturally in English, Hindi, or mixed PWD terms.")
        wav_path = engine.record()
        print("🧠 Transcribing speech...")
        raw_text = engine.transcribe(wav_path)
        if not raw_text.strip():
            print("  ⚠️ No speech detected.")
            return

        print(f"  Recognized: \"{raw_text}\"")
        res = process_input(raw_text, mode=mode)
        if res["type"] == "abbreviation":
            out = f"  [{res['category']}] {res['input']} = {res['meaning']}"
            print(out)
            if copy:
                copy_to_clipboard(f"{res['input']} — {res['meaning']}")
                print("  📋 Copied to clipboard!")
        else:
            out = f"  Hindi ({res['method']}): {res['translation']}"
            print(out)
            if copy:
                copy_to_clipboard(res["translation"])
                print("  📋 Copied to clipboard!")
    except Exception as exc:
        print(f"  ❌ Voice processing error: {exc}")


def run_repl(initial_mode: str = "auto"):
    """Interactive Read-Eval-Print Loop with voice and dictionary commands."""
    mode = initial_mode
    print("=" * 60)
    print("🏛  PWD Uttarakhand — Hybrid Language Helper & Terminology")
    print("=" * 60)
    print("Commands:")
    print("  • Type any abbreviation (e.g. EE, NIT, MB) -> English & Hindi designation")
    print("  • Type any sentence                         -> Hindi translation")
    print("  • search <term>                             -> Search abbreviations")
    print("  • list                                      -> List all 50+ abbreviations")
    print("  • v  (or voice)                             -> 🎙 Record voice & lookup/translate")
    print("  • add <ABBR>=<Meaning>                      -> Add custom abbreviation")
    print("  • mode <offline|online|auto>                -> Change translation mode")
    print("  • exit / quit                               -> Exit\n")

    while True:
        try:
            user_input = input(f"[{mode}] >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("exit", "quit", "q"):
            print("Goodbye.")
            break

        if cmd in ("v", "voice", "mic"):
            run_voice_input(mode=mode, copy=True)
            continue

        if cmd.startswith("mode "):
            new_mode = user_input.split(None, 1)[1].lower()
            if new_mode in ("offline", "online", "auto"):
                mode = new_mode
                print(f"  Switched to {mode} translation mode.")
            else:
                print("  Invalid mode. Choose: offline, online, or auto.")
            continue

        if cmd == "list":
            grouped = list_by_category()
            for cat, terms in sorted(grouped.items()):
                print(f"\n📂 [{cat.upper()}]:")
                for abbr, meaning in sorted(terms.items()):
                    print(f"  • {abbr} = {meaning}")
            continue

        if cmd.startswith("search "):
            term = user_input.split(None, 1)[1]
            matches = search_abbreviations(term)
            if not matches:
                print(f"  No abbreviations found matching '{term}'")
            else:
                for abbr, info in sorted(matches.items()):
                    print(f"  [{info['category']}] {abbr} = {info['meaning']}")
            continue

        if cmd.startswith("add ") and "=" in user_input:
            body = user_input[4:].strip()
            abbr, meaning = body.split("=", 1)
            ok = add_custom_abbreviation(abbr.strip(), meaning.strip())
            if ok:
                print(f"  ✅ Added custom abbreviation: {abbr.strip().upper()} = {meaning.strip()}")
            else:
                print("  ❌ Failed to save custom abbreviation.")
            continue

        # Standard process
        try:
            res = process_input(user_input, mode=mode)
            if res["type"] == "abbreviation":
                print(f"  [{res['category']}] {res['input']} = {res['meaning']}")
                copy_to_clipboard(f"{res['input']} — {res['meaning']}")
            else:
                print(f"  Hindi ({res['method']}): {res['translation']}")
                copy_to_clipboard(res["translation"])
        except Exception as e:
            print(f"  Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="PWD Uttarakhand Language Helper & Terminology Tool")
    parser.add_argument("query", nargs="*", help="Optional abbreviation or sentence for one-shot lookup")
    parser.add_argument("-c", "--copy", action="store_true", help="Copy result to clipboard")
    parser.add_argument("-m", "--mode", choices=["auto", "offline", "online"], default="auto", help="Translation mode")
    parser.add_argument("-v", "--voice", action="store_true", help="Trigger microphone voice input")
    args = parser.parse_args()

    if args.voice:
        run_voice_input(mode=args.mode, copy=True)
    elif args.query:
        query_str = " ".join(args.query)
        run_one_shot(query_str, mode=args.mode, copy=args.copy)
    else:
        run_repl(initial_mode=args.mode)


if __name__ == "__main__":
    main()
