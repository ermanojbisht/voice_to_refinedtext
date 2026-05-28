#!/usr/bin/env python3
"""Evening review reminder — fires at configured time if no review completed today.

Run via the systemd user timer installed by install_evening_reminder.sh.
Skips silently if:
  - evening_reminder_enabled is false in review_config.json
  - a review was already completed today (last_date in streak.json matches today)
  - a review is currently in progress
"""
import os
import sys
import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import review_engine


def main():
    review_engine.init_logging(script_dir)
    config = review_engine.load_review_config(script_dir)
    if not config.get("evening_reminder_enabled", False):
        return

    today = datetime.date.today().isoformat()

    # Skip if review already completed today
    streak = review_engine.load_streak(script_dir)
    if streak.get("last_date") == today:
        return

    # Skip if a review is currently in progress
    active, _ = review_engine.is_review_active(script_dir)
    if active:
        return

    msg = "🌙 Evening Review not done yet. Start it from the tray app."
    review_engine.send_notification("Evening Review Reminder", msg)
    review_engine.send_telegram(msg, config)
    review_engine._rlog("evening_reminder: sent")


if __name__ == "__main__":
    main()
