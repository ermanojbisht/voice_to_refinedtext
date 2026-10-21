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


def run_voice_input(mode: str = "auto", copy: bool = True, use_hud: bool = True, pipe: bool = False, read_result: bool = False):
    """Captures microphone speech, transcribes, and runs PWD lookup/translation."""
    try:
        from engine import VoiceEngine
        engine = VoiceEngine(SCRIPT_DIR)

        # Retrieve active preset & refinement goal metadata for HUD
        preset_key = engine.get_active_preset()
        preset_cfg = engine.config.get("ASR_PRESETS", {}).get(preset_key, {})
        preset_label = preset_cfg.get("label", preset_key)

        goal_key = engine.config.get("ACTIVE_REFINEMENT_GOAL", "clean_bilingual")
        goal_cfg = engine.config.get("REFINEMENT_GOALS", {}).get(goal_key, {})
        goal_label = goal_cfg.get("label", goal_key)

        # Check if HUD is enabled in config and CLI flags
        hud_enabled = use_hud and engine.config.get("CLI_RICH_HUD", True)
        from pwd_helper.terminal_hud import TerminalHUD
        hud = TerminalHUD(
            enabled=hud_enabled,
            pipe_mode=pipe,
            preset_label=preset_label,
            goal_label=goal_label,
        )

        hud.start_listening()
        wav_path = engine.record(on_audio_chunk=lambda chunk, energy=None: hud.update_audio(chunk, energy))

        hud.set_state("TRANSCRIBING")
        raw_text = engine.transcribe(wav_path)

        if not raw_text.strip():
            hud.set_state("DONE", detail="No speech detected.")
            hud.close()
            if not pipe:
                print("⚠️ No speech detected.", file=sys.stderr if pipe else sys.stdout)
            return

        hud.set_state("REFINING")
        if mode == "raw":
            final_text = raw_text
        else:
            res = process_input(raw_text, mode=mode)
            if res["type"] == "abbreviation":
                final_text = f"[{res['category']}] {res['input']} = {res['meaning']}"
            else:
                final_text = res.get("translation", raw_text)

        hud.finish(final_text)

        # Output to stdout
        if pipe:
            sys.stdout.write(final_text + "\n")
            sys.stdout.flush()
        else:
            print(f"Recognized: {final_text}")

        if copy:
            copy_to_clipboard(final_text)
            if not pipe:
                print("  📋 Copied to clipboard!")

        if read_result and final_text:
            import pwd_helper.tts as tts
            tts.speak(final_text, blocking=False)

    except Exception as exc:
        print(f"❌ Voice processing error: {exc}", file=sys.stderr)


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


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser for pwd_cli."""
    parser = argparse.ArgumentParser(description="PWD Uttarakhand Language Helper & Terminology Tool")
    parser.add_argument("query", nargs="*", help="Optional abbreviation or sentence for one-shot lookup")
    parser.add_argument("-c", "--copy", action="store_true", help="Copy result to clipboard")
    parser.add_argument(
        "-m",
        "--mode",
        choices=["raw", "auto", "offline", "online"],
        default=None,
        help="Mode: raw (clean speech dictation), auto/offline/online (translate to Hindi)",
    )
    parser.add_argument("-v", "--voice", "-l", "--listen", action="store_true", help="Trigger microphone voice input")
    parser.add_argument("-p", "--pipe", action="store_true", help="Output raw refined text only (suitable for UNIX pipes)")
    parser.add_argument("--hud", dest="hud", action="store_true", default=None, help="Force enable Rich terminal HUD")
    parser.add_argument("--no-hud", dest="hud", action="store_false", help="Disable Rich HUD (plain text output)")
    # Speech Synthesis (TTS) flags
    parser.add_argument("-s", "--speak", type=str, default=None, help="Speak provided text aloud")
    parser.add_argument("--speak-file", type=str, default=None, help="Read Markdown or text document aloud")
    parser.add_argument("--stop-speech", action="store_true", help="Immediately stop active speech playback")
    parser.add_argument("-r", "--read-result", action="store_true", help="Read back the refined transcription aloud when dictating")
    parser.add_argument("--tts-voice", type=str, default=None, help="TTS voice preset: ni_delhi_corp_f, ni_kahani_f, ni_air_anchor_m, ni_ncr_tech_m, ni_fm_rj_f, ni_docu_deep_m (or en_in_female, en_in_male, hf_alpha, hm_omega)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Handle direct TTS speech commands first
    if args.stop_speech:
        import pwd_helper.tts as tts
        tts.stop()
        print("🛑 Speech stopped.")
        return

    tts_cfg = {
        "voice": args.tts_voice,
        "kokoro_voice": args.tts_voice,
        "kokoro_voice_en": args.tts_voice,
        "kokoro_voice_hi": args.tts_voice,
    } if args.tts_voice else None

    if args.speak:
        import pwd_helper.tts as tts
        text_to_speak = sys.stdin.read() if args.speak == "-" else args.speak
        tts.speak(text_to_speak, blocking=True, config=tts_cfg)
        return

    if args.speak_file:
        import pwd_helper.tts as tts
        file_path = os.path.expanduser(args.speak_file)
        if not os.path.isfile(file_path):
            print(f"❌ File not found: {args.speak_file}", file=sys.stderr)
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tts.speak(content, blocking=True, config=tts_cfg)
        return

    use_hud = True if args.hud is None else args.hud
    active_mode = args.mode if args.mode is not None else ("raw" if args.voice else "auto")

    if args.voice:
        run_voice_input(mode=active_mode, copy=not args.pipe, use_hud=use_hud, pipe=args.pipe, read_result=args.read_result)
    elif args.query:
        query_str = " ".join(args.query)
        run_one_shot(query_str, mode=active_mode, copy=args.copy)
    else:
        run_repl(initial_mode=active_mode)


if __name__ == "__main__":
    main()
