#!/usr/bin/env python3
"""Morning Priority Briefing — reads yesterday's Tomorrow's Priorities and narrates them.

Run automatically via a systemd user timer (install_morning_brief.sh), or manually:
    python3 morning_brief.py

State is written to /tmp/morning_brief_state.json so the tray can replay it on demand.
"""
import os
import sys
import json
import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import review_engine

BRIEF_STATE = "/tmp/morning_brief_state.json"


def _get_priorities(script_dir, config):
    """Return (priorities_text, note_date_str) from yesterday's Evening Review.
    Returns (None, yesterday_str) if the note or section is missing.
    """
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    note_path = review_engine._get_daily_note_path(script_dir, config, yesterday)

    if not os.path.exists(note_path):
        review_engine._rlog(f"morning_brief: no daily note for {yesterday}: {note_path}")
        return None, yesterday

    evening_review = review_engine._extract_evening_review_section(note_path)
    if not evening_review:
        review_engine._rlog(f"morning_brief: no Evening Review section in {note_path}")
        return None, yesterday

    priorities = review_engine._extract_step_section("Tomorrow's Priorities", evening_review)
    if not priorities:
        review_engine._rlog(f"morning_brief: no Tomorrow's Priorities in {yesterday}")
        return None, yesterday

    return priorities, yesterday


def _save_brief_state(text, date_str):
    state = {
        "text": text,
        "date": date_str,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    try:
        with open(BRIEF_STATE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        review_engine._rlog(f"morning_brief: state saved to {BRIEF_STATE}")
    except Exception as e:
        review_engine._rlog(f"morning_brief: state save error: {e}")


def load_brief_state():
    """Return saved morning brief state dict, or None if not found / stale."""
    try:
        with open(BRIEF_STATE, "r", encoding="utf-8") as f:
            state = json.load(f)
        # Expire state if it's from a previous day
        saved_date = state.get("date", "")
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        if saved_date != yesterday:
            return None
        return state
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def run_morning_brief(script_dir):
    review_engine.init_logging(script_dir)
    review_engine._rlog("=" * 50)
    review_engine._rlog("morning_brief: starting")

    config = review_engine.load_review_config(script_dir)

    if not config.get("morning_briefing_enabled", False):
        review_engine._rlog("morning_brief: disabled in config, exiting")
        return

    priorities, date_str = _get_priorities(script_dir, config)

    if not priorities:
        review_engine.send_notification(
            "🌅 Morning Brief",
            f"No priorities found from {date_str}. Do an evening review tonight!"
        )
        review_engine._rlog("morning_brief: no priorities found, notified user")
        return

    _save_brief_state(priorities, date_str)

    lang = config.get("context_brief_language", "en")
    if lang == "hi":
        intro = f"गुड मॉर्निंग! कल की प्राथमिकताएं:\n{priorities}"
    else:
        intro = f"Good morning! Here are your priorities for today:\n{priorities}"

    review_engine.send_notification("🌅 Morning Brief", priorities[:240])
    review_engine.narrate(intro, config, blocking=True)
    review_engine._rlog("morning_brief: done")


if __name__ == "__main__":
    run_morning_brief(script_dir)
