#!/usr/bin/env python3
import os
import re
import json
import datetime
import subprocess
import threading
import collections

import utils as _utils

STATE_PATH             = "/tmp/review_state.json"
_PROCESSING_LOCK_PATH  = "/tmp/review_processing.lock"
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Module-level logger — file handler added by init_logging() at startup
_logger = _utils.get_logger("review_engine")


def _rlog(msg):
    """Compatibility shim — internal and external callers still use _rlog()."""
    _logger.info(msg)


def init_logging(script_dir):
    """Configure file logging. Called once at startup by tray_app and review_dashboard."""
    log_path = os.path.join(script_dir, "review_debug.log")
    _utils.get_logger("review_engine", log_path)
    try:
        import telegram_service
        telegram_service.set_logger(_rlog)
    except ImportError:
        pass

# ── Config ────────────────────────────────────────────────────────────────────

def load_review_config(script_dir):
    config_path = os.path.join(script_dir, "review_config.json")
    default_config = {
        "vault_paths": {
            "base_vault": "~/learning_vault",
            "daily_notes": "~/learning_vault/My Daily Notes",
            "wellness_notes": "~/learning_vault/My Daily Notes/Wellness"
        },
        "review_expiry_hours": 1,
        "last_n_days_context": 3,
        "per_step_context": False,
        "voice_narration": True,
        "tts_engine": "espeak",   # "espeak" or "piper"
        "piper_model": "",        # path to English .onnx model file (only used when tts_engine="piper")
        "piper_model_hi": "",     # path to Hindi .onnx model file (falls back to piper_model if empty)
        "carryforward_tasks": False,   # read yesterday's - [ ] items and narrate at step
        "carryforward_step_id": 3,     # step_id at which to narrate + show pending tasks
        "show_streak": True,           # narrate + display consecutive-review streak
        "focus_word_trend": True,      # append focus word to focus_words.jsonl; narrate weekly trend on Sundays
        "morning_briefing_enabled": False,  # narrate Tomorrow's Priorities each morning
        "morning_briefing_time": "08:00",   # HH:MM — used by install_morning_brief.sh to set the systemd timer
        "voice_control": False,             # opt-in: listen for "stop"/"again" keywords during narration
        "voice_control_threshold": 500,     # energy gate in int16-scale RMS; raise if TTS bleed triggers false positives
        "evening_reminder_enabled": False,  # send reminder if review not done by reminder time
        "evening_reminder_time": "21:00",   # HH:MM — used by install_evening_reminder.sh
        "pending_task_lookback_days": 7,    # how many past daily notes to scan for recurring unchecked tasks (0 = off)
        "pending_task_warn_threshold": 3,   # days pending before ⚠️ label in morning brief story
        "pending_task_critical_threshold": 5,  # days pending before 🚨 label
        "telegram_enabled": False,          # send key events to Telegram on mobile
        "telegram_bot_token": "",           # from @BotFather
        "telegram_chat_id": "",             # your personal chat ID
        "review_steps": [
            {
                "step_id": 1,
                "section_name": "Focus Word",
                "prompt_notification": "Step 1/6: Speak today's core focus word or overarching theme.",
                "section_fill": False,
                "isolate_file": False,
                "skippable": True,
                "refine": True,
                "structure_prompt": (
                    "Extract the single core focus word or theme from this voice note. "
                    "Output only the word or short phrase, nothing else:\n{raw_text}"
                )
            },
            {
                "step_id": 2,
                "section_name": "Achievements",
                "prompt_notification": "Step 2/6: What did you accomplish, build, or unblock today?",
                "section_fill": False,
                "isolate_file": False,
                "skippable": True,
                "refine": True,
                "structure_prompt": (
                    "Convert this voice note into a concise bullet-point list of achievements. "
                    "Each bullet must start with a past-tense action verb. "
                    "Output only the bullet points, no headings:\n{raw_text}"
                )
            },
            {
                "step_id": 3,
                "section_name": "Tomorrow's Priorities",
                "prompt_notification": "Step 3/6: What tasks need immediate attention tomorrow?",
                "section_fill": False,
                "isolate_file": False,
                "skippable": True,
                "refine": True,
                "structure_prompt": (
                    "Convert this voice note into a Markdown checkbox task list for tomorrow. "
                    "Format each item as '- [ ] task description'. "
                    "Output only the checkbox list, no headings:\n{raw_text}"
                )
            },
            {
                "step_id": 4,
                "section_name": "Wellness Log",
                "prompt_notification": "Step 4/6: Any wellness or personal reflections? (Speak or Skip).",
                "section_fill": False,
                "isolate_file": True,
                "skippable": True,
                "refine": False,
                "structure_prompt": ""
            },
            {
                "step_id": 5,
                "section_name": "Meeting",
                "prompt_notification": "Step 5/6: Summarise today's meetings — decisions made and actions assigned.",
                "section_fill": True,
                "isolate_file": False,
                "skippable": True,
                "refine": True,
                "structure_prompt": (
                    "Summarise this meeting note into structured bullet points. "
                    "Group under two sub-sections: 'Decisions:' and 'Actions:'. "
                    "Output only the bullet points:\n{raw_text}"
                )
            },
            {
                "step_id": 6,
                "section_name": "Movement",
                "prompt_notification": "Step 6/6: Any movement, exercise, or physical activity today?",
                "section_fill": True,
                "isolate_file": False,
                "skippable": True,
                "refine": True,
                "skip_default": "only office",
                "structure_prompt": (
                    "Summarise this movement or physical activity note in 1-2 plain sentences:\n{raw_text}"
                )
            }
        ]
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            if "vault_paths" in user_config and isinstance(user_config["vault_paths"], dict):
                default_config["vault_paths"].update(user_config["vault_paths"])
                user_config.pop("vault_paths")
            if "review_steps" in user_config:
                # Merge per-step overrides by step_id
                user_steps = {s["step_id"]: s for s in user_config.pop("review_steps") if "step_id" in s}
                for step in default_config["review_steps"]:
                    if step["step_id"] in user_steps:
                        step.update(user_steps[step["step_id"]])
            default_config.update(user_config)
        except Exception as e:
            _rlog(f"load_review_config: error reading user config (using defaults): {e}")
    return default_config


# ── Review session log ────────────────────────────────────────────────────────

_REVIEW_LOG_FILE = "review_log.json"


def _log_review(script_dir, entry):
    """Append one entry to review_log.json.

    Each entry has at minimum: timestamp, session_date, step_id, step_name, event.
    Two event types:
      'clip_recorded'  — raw Whisper text captured for a step
      'step_structured' — final text written to the vault for a step
    Never raises; log failures are swallowed so they don't interrupt the review.
    """
    try:
        entry["timestamp"] = datetime.datetime.now().isoformat()
        log_path = os.path.join(script_dir, _REVIEW_LOG_FILE)
        data = []
        if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
            with open(log_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
        data.append(entry)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        _rlog(f"_log_review: failed to write review_log.json: {e}")


# ── State I/O ─────────────────────────────────────────────────────────────────

import fcntl as _fcntl


def _acquire_processing_lock():
    """Try to acquire the exclusive processing lock with LOCK_NB (non-blocking).

    Returns an open file descriptor on success.
    Returns None immediately if another process already holds the lock.

    The caller MUST pass the returned fd to _release_processing_lock() in a finally block.
    On Linux, flock() locks are released automatically if the process exits or crashes,
    so there is no risk of a stale lock blocking future operations.
    """
    fd = None
    try:
        fd = open(_PROCESSING_LOCK_PATH, "w")
        _fcntl.flock(fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
        return fd
    except (BlockingIOError, OSError):
        # Another process holds the lock — bail immediately, do not block.
        if fd is not None:
            try:
                fd.close()
            except Exception:
                pass
        return None


def _release_processing_lock(fd):
    """Release the exclusive lock and close the fd returned by _acquire_processing_lock()."""
    if fd is None:
        return
    try:
        _fcntl.flock(fd, _fcntl.LOCK_UN)
    except Exception:
        pass
    try:
        fd.close()
    except Exception:
        pass


def _save_state(state):
    # Write to a temp file then atomically rename so readers never see a partial file.
    # flock on the temp file ensures only one writer serialises at a time.
    tmp = STATE_PATH + ".tmp"
    try:
        payload = json.dumps(state, indent=2)
        with open(tmp, "w", encoding="utf-8") as f:
            _fcntl.flock(f, _fcntl.LOCK_EX)
            try:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            finally:
                _fcntl.flock(f, _fcntl.LOCK_UN)
        os.replace(tmp, STATE_PATH)  # atomic on POSIX
        _rlog(f"State saved: step={state.get('current_step_index')}, awaiting={state.get('awaiting_more')}")
    except Exception as e:
        _rlog(f"ERROR saving state: {e}")
        try:
            os.unlink(tmp)
        except OSError:
            pass


def load_state():
    if not os.path.exists(STATE_PATH):
        # Absence of state file is a normal condition — no log here to avoid
        # flooding the log every 500 ms when the dashboard polls after completion.
        return None
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            _fcntl.flock(f, _fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                _fcntl.flock(f, _fcntl.LOCK_UN)
    except json.JSONDecodeError:
        _rlog("ERROR loading state: JSONDecodeError — file may be mid-write")
    except Exception as e:
        _rlog(f"ERROR loading state: {e}")
    return None


def is_review_active(script_dir):
    state = load_state()
    if state is None:
        _rlog("is_review_active → False (no state file)")
        return False, None
    if not state.get("active", False):
        _rlog("is_review_active → False (active=False in state)")
        return False, None

    # Check that the SESSION was started today, not that the note date matches today.
    # This allows reviews for past dates (state["date"] may be any date the user chose).
    try:
        started_date = datetime.datetime.fromisoformat(state["started_at"]).date().isoformat()
        today = datetime.date.today().isoformat()
        if started_date != today:
            _rlog(f"is_review_active → False (session started on {started_date}, not today)")
            return False, None
    except Exception as e:
        _rlog(f"is_review_active: started_at parse error (ignored): {e}")

    config = load_review_config(script_dir)
    expiry_hours = config.get("review_expiry_hours", 1)
    try:
        started_at = datetime.datetime.fromisoformat(state["started_at"])
        elapsed = (datetime.datetime.now() - started_at).total_seconds() / 3600
        if elapsed > expiry_hours:
            _rlog(f"is_review_active → False (expired: {elapsed:.2f}h > {expiry_hours}h)")
            return False, None
    except Exception as e:
        _rlog(f"is_review_active: expiry check error (ignored): {e}")

    return True, state


# ── Path helpers ──────────────────────────────────────────────────────────────

def get_daily_note_path(script_dir, config, date_str=None):
    """Returns YYYY/MonthName/YYYY-MM-DD.md path under daily_notes base."""
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    dt = datetime.date.fromisoformat(date_str)
    year = dt.strftime("%Y")
    month = dt.strftime("%B")   # Full English month name
    vault_paths = config.get("vault_paths", {})
    base = os.path.expanduser(vault_paths.get("daily_notes", "~/learning_vault/My Daily Notes"))
    return os.path.join(base, year, month, f"{date_str}.md")


def _get_wellness_note_path(script_dir, config, date_str=None):
    """Returns YYYY/MonthName/YYYY-MM-DD.md path under wellness_notes base."""
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    dt = datetime.date.fromisoformat(date_str)
    year = dt.strftime("%Y")
    month = dt.strftime("%B")
    vault_paths = config.get("vault_paths", {})
    base = os.path.expanduser(vault_paths.get("wellness_notes", "~/learning_vault/My Daily Notes/Wellness"))
    return os.path.join(base, year, month, f"{date_str}.md")


# ── Note file helpers ─────────────────────────────────────────────────────────

def _ordinal(n):
    """Return number with correct English ordinal suffix: 1st, 2nd, 3rd, 4th…"""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]}"


def _render_template(template_path, tokens):
    """Read a template file and substitute {{token}} placeholders.

    Falls back to returning None if the file doesn't exist, so callers can
    supply a hardcoded fallback string.
    """
    if not os.path.exists(template_path):
        return None
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        for key, value in tokens.items():
            content = content.replace("{{" + key + "}}", value)
        return content
    except Exception as e:
        _rlog(f"_render_template: failed to read {template_path}: {e}")
        return None


def _create_wellness_note(file_path, date_str):
    """Create a wellness note using templates/wellness_note.md (with hardcoded fallback)."""
    now = datetime.datetime.now()
    now_str = now.strftime(f"%A {_ordinal(now.day)} %B %Y %H:%M:%S")
    tokens = {"date": date_str, "mod_date": now_str}

    template_path = os.path.join(_SCRIPT_DIR, "templates", "wellness_note.md")
    content = _render_template(template_path, tokens)
    if content is None:
        content = (
            f"---\n"
            f"creation date: {date_str}\n"
            f"modification date: {now_str}\n"
            f"---\n\n"
            f"# Wellness — {date_str}\n\n"
        )
        _rlog("_create_wellness_note: template file not found, using hardcoded fallback")

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    _rlog(f"_create_wellness_note: created {file_path}")


def _create_daily_note(file_path, date_str):
    """Create a daily note using templates/daily_note.md (with hardcoded fallback)."""
    dt = datetime.date.fromisoformat(date_str)
    prev_day = (dt - datetime.timedelta(days=1)).isoformat()
    next_day = (dt + datetime.timedelta(days=1)).isoformat()
    now = datetime.datetime.now()
    now_str = now.strftime(f"%A {_ordinal(now.day)} %B %Y %H:%M:%S")
    tokens = {
        "date":     date_str,
        "prev_day": prev_day,
        "next_day": next_day,
        "mod_date": now_str,
    }

    template_path = os.path.join(_SCRIPT_DIR, "templates", "daily_note.md")
    content = _render_template(template_path, tokens)
    if content is None:
        content = (
            f"---\n"
            f"creation date: {date_str}\n"
            f"modification date: {now_str}\n"
            f"---\n\n"
            f"<< [[{prev_day}]] | [[{next_day}]] >>\n\n"
            f"# {date_str}\n\n"
            f"### Movement\n\n"
            f"### Meeting\n\n"
            f"### Achievements\n\n"
            f"### Tomorrow's Priorities\n\n"
            f"### Focus Word\n\n"
        )
        _rlog("_create_daily_note: template file not found, using hardcoded fallback")

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    _rlog(f"_create_daily_note: created {file_path}")


def _ensure_evening_review_section(file_path):
    """Append ## Evening Review header if not already in the file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if not re.search(r'^## Evening Review\s*$', content, re.MULTILINE):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("\n## Evening Review\n\n")
        _rlog(f"_ensure_evening_review_section: added section to {file_path}")


# ── Last-N-days context ────────────────────────────────────────────────────────

def extract_evening_review_section(note_path):
    """Extract all named review sections (### …) from a daily note for context.

    No longer requires a ## Evening Review parent header — reads any ### section
    whose name is not 'Audio'. Falls back gracefully on old-format notes that still
    have a ## Evening Review header.
    """
    _SKIP_SECTIONS = {"Audio"}
    try:
        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Split on any ### header; collect (name, body) pairs
        parts = re.split(r'^### (.+)$', content, flags=re.MULTILINE)
        # parts = [pre, name, body, name, body, ...]
        collected = []
        i = 1
        while i + 1 < len(parts):
            name = parts[i].strip()
            body = parts[i + 1].strip()
            i += 2
            if name in _SKIP_SECTIONS or not body:
                continue
            collected.append(f"**{name}**\n{body}")
        if collected:
            return "\n\n".join(collected)
    except Exception:
        pass
    return ""


def extract_step_section(section_name, evening_review_content):
    """Extract text under a section from an evening review content string.

    extract_evening_review_section converts ### headings to **bold** format,
    so we search for **SectionName** rather than ### SectionName.
    """
    m = re.search(
        r'^\*\*' + re.escape(section_name) + r'\*\*\s*\n(.*?)(?=^\*\*|\Z)',
        evening_review_content, re.MULTILINE | re.DOTALL
    )
    if m:
        return m.group(1).strip()
    return ""


# ── Pending task story helpers ────────────────────────────────────────────────

def _parse_priority_tasks(text):
    """Parse markdown checkbox lines from a Tomorrow's Priorities section.

    Returns a list of {"text": str, "done": bool} dicts, one per task line.
    Non-task lines (blank, headings, prose) are silently skipped.
    """
    tasks = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- [x] ") or line.startswith("- [X] "):
            tasks.append({"text": line[6:].strip(), "done": True})
        elif line.startswith("- [ ] "):
            tasks.append({"text": line[6:].strip(), "done": False})
    return tasks


def _normalize_task(text):
    """Lowercase, strip punctuation, compress whitespace — for cross-day matching."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def _tasks_match(norm_a, norm_b):
    """Return True if two already-normalised task strings refer to the same task.

    Exact match first; falls back to word-overlap ≥ 70 % to handle minor
    LLM rephrasing between days (e.g. "Resolve errors with officers" vs
    "Fix field officer data entry errors").
    """
    if norm_a == norm_b:
        return True
    words_a = set(norm_a.split())
    words_b = set(norm_b.split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
    return overlap >= 0.60


def get_pending_tasks(script_dir, config):
    """Scan the last N daily notes and return tasks that are still unchecked.

    Scans ALL days in the lookback window (not just yesterday) so tasks that
    were written several days ago but never carried forward are still surfaced.

    Config keys used:
      pending_task_lookback_days  — how many days to scan (default 7; 0 = off)

    Returns a list of dicts sorted by days_pending descending:
      {"text": str, "days_pending": int, "first_seen": ISO-date str}
    Returns [] when the feature is disabled or no pending tasks exist.
    """
    lookback = config.get("pending_task_lookback_days", 7)
    if not lookback:
        return []

    today = datetime.date.today()

    # ── Step 1: scan ALL days in lookback window ──────────────────────────────
    # day_data: list of {"date": str, "tasks": list|None}, most-recent first
    day_data = []
    for i in range(1, lookback + 1):
        day_str = (today - datetime.timedelta(days=i)).isoformat()
        note_path = get_daily_note_path(script_dir, config, day_str)
        if not os.path.exists(note_path):
            day_data.append({"date": day_str, "tasks": None})
            continue
        evening = extract_evening_review_section(note_path)
        priorities_text = extract_step_section("Tomorrow's Priorities", evening)
        day_data.append({"date": day_str, "tasks": _parse_priority_tasks(priorities_text)})

    # ── Step 2: build "done" set — task checked on ANY day means it's complete ─
    done_norms = set()
    for day_info in day_data:
        if day_info["tasks"]:
            for task in day_info["tasks"]:
                if task["done"]:
                    done_norms.add(_normalize_task(task["text"]))

    # ── Step 3: collect all unique unchecked tasks across all days ────────────
    # Track by normalised text → earliest date seen (to compute days_pending)
    seen: dict = {}   # norm -> {"text": str, "first_seen": str}
    for day_info in day_data:
        if not day_info["tasks"]:
            continue
        for task in day_info["tasks"]:
            if task["done"]:
                continue
            norm = _normalize_task(task["text"])
            if any(_tasks_match(norm, d) for d in done_norms):
                continue   # completed on some other day
            if norm not in seen:
                seen[norm] = {"text": task["text"], "first_seen": day_info["date"]}
            else:
                # day_data is most-recent-first, so later entries are older
                seen[norm]["first_seen"] = day_info["date"]

    # ── Step 4: build result list ─────────────────────────────────────────────
    pending = []
    for norm, info in seen.items():
        first_dt = datetime.date.fromisoformat(info["first_seen"])
        days_pending = (today - first_dt).days
        pending.append({
            "text": info["text"],
            "days_pending": days_pending,
            "first_seen": info["first_seen"],
        })
        _rlog(f"pending_tasks: '{info['text'][:40]}' — {days_pending} day(s)")

    pending.sort(key=lambda x: x["days_pending"], reverse=True)
    return pending


def build_pending_story(pending_tasks, config):
    """Build a narrative for pending tasks suitable for TTS and notifications.

    Returns {"narration": str, "display": str}:
      narration — emoji-free text for TTS (piper / espeak both struggle with emojis)
      display   — emoji-labelled text for desktop notifications and Telegram

    Label thresholds (from config):
      >= critical_threshold  → 🚨  (default 5 days)
      >= warn_threshold      → ⚠️   (default 3 days)
      2 days                 → 📌
      1 day                  → 🆕
    """
    if not pending_tasks:
        return {"narration": "", "display": ""}

    lang = config.get("context_brief_language", "en")
    warn = config.get("pending_task_warn_threshold", 3)
    crit = config.get("pending_task_critical_threshold", 5)
    max_days = pending_tasks[0]["days_pending"]   # list is sorted desc
    count = len(pending_tasks)

    lines_display = []
    lines_narrate = []

    for t in pending_tasks:
        n = t["days_pending"]
        text = t["text"]
        if lang == "hi":
            if n >= crit:
                label_d, label_n = f"🚨 {n} दिनों से लंबित", f"{n} दिनों से लंबित"
            elif n >= warn:
                label_d, label_n = f"⚠️ {n} दिनों से", f"{n} दिनों से"
            elif n == 2:
                label_d, label_n = "📌 2 दिनों से", "2 दिनों से"
            else:
                label_d, label_n = "🆕 आज नया", "नया"
        else:
            if n >= crit:
                label_d, label_n = f"🚨 {n} days pending", f"{n} days pending"
            elif n >= warn:
                label_d, label_n = f"⚠️ {n} days", f"{n} days"
            elif n == 2:
                label_d, label_n = "📌 2 days", "2 days"
            else:
                label_d, label_n = "🆕 New today", "New"
        lines_display.append(f"{label_d} — {text}")
        lines_narrate.append(f"{label_n}: {text}")

    if lang == "hi":
        header_d = f"📋 {count} लंबित कार्य:"
        header_n = f"आपके {count} लंबित कार्य हैं।"
        footer = (f"सबसे पुराना कार्य {max_days} दिनों से है — इसे आज प्राथमिकता दें।"
                  if max_days > 1 else "")
    else:
        header_d = f"📋 {count} pending task{'s' if count > 1 else ''}:"
        header_n = f"You have {count} pending task{'s' if count > 1 else ''}."
        footer = (f"Your oldest pending task is {max_days} days old — consider making it today's priority."
                  if max_days > 1 else "")

    display = header_d + "\n" + "\n".join(lines_display)
    if footer:
        display += "\n" + footer

    narration = header_n + " " + ". ".join(lines_narrate)
    if footer:
        narration += ". " + footer

    return {"narration": narration, "display": display}


def _strip_frontmatter(lines):
    """Return index of first content line after YAML frontmatter (--- ... ---) and any title heading."""
    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i += 1  # skip closing ---
    # Skip blank lines and top-level title heading (# Title)
    while i < len(lines) and (not lines[i].strip() or lines[i].startswith("# ")):
        i += 1
    return i


def _read_isolated_note_content(file_path):
    """Read an isolated note file and return its body text (strips YAML frontmatter and title heading)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        return ""
    lines = raw.splitlines()
    return "\n".join(lines[_strip_frontmatter(lines):]).strip()


def get_isolated_notes(script_dir, config, n, before_date_str):
    """Return [{date, content}] for the last n days of an isolated (e.g. Wellness) note file."""
    results = []
    try:
        base_dt = datetime.date.fromisoformat(before_date_str)
    except Exception:
        return results
    for i in range(1, n + 1):
        day = base_dt - datetime.timedelta(days=i)
        day_str = day.isoformat()
        note_path = _get_wellness_note_path(script_dir, config, day_str)
        if not os.path.exists(note_path):
            continue
        content = _read_isolated_note_content(note_path)
        if content:
            results.append({"date": day_str, "content": content})
    return results


def _read_last_n_notes(script_dir, config, n, before_date_str):
    """Return [{date, content}] for last n days before before_date_str that have ## Evening Review content."""
    results = []
    try:
        base_dt = datetime.date.fromisoformat(before_date_str)
    except Exception:
        return results
    for i in range(1, n + 1):
        day = base_dt - datetime.timedelta(days=i)
        day_str = day.isoformat()
        note_path = get_daily_note_path(script_dir, config, day_str)
        if not os.path.exists(note_path):
            _rlog(f"context: no note for {day_str}")
            continue
        section = extract_evening_review_section(note_path)
        if section:
            results.append({"date": day_str, "content": section})
            _rlog(f"context: loaded {day_str} ({len(section)} chars)")
        else:
            _rlog(f"context: note exists for {day_str} but no Evening Review section")
    return results


# ── Brief cache helpers ───────────────────────────────────────────────────────

def _brief_cache_path(script_dir):
    return os.path.join(script_dir, "brief_cache.json")


def _load_brief_cache(script_dir, date_str):
    """Return cached {en, hi} dict for date_str, or None if missing."""
    try:
        with open(_brief_cache_path(script_dir), "r", encoding="utf-8") as f:
            cache = json.load(f)
        entry = cache.get(date_str)
        if entry and entry.get("en") and entry.get("hi"):
            # Reject stale fallback text written before the no-cache-on-failure fix.
            # These entries look like "Notes loaded for N day(s). AI synthesis unavailable."
            if entry["en"].startswith("Notes loaded for"):
                _rlog(f"context_brief: stale fallback in cache for {date_str} — ignoring, will regenerate")
                return None
            _rlog(f"context_brief: cache hit for {date_str}")
            return entry
    except FileNotFoundError:
        pass
    except Exception as e:
        _rlog(f"context_brief: cache load error: {e}")
    return None


def _bust_brief_cache(script_dir, date_str):
    """Remove today's entry from brief_cache.json so next call regenerates."""
    path = _brief_cache_path(script_dir)
    try:
        try:
            with open(path, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return
        if date_str in cache:
            del cache[date_str]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            _rlog(f"context_brief: cache busted for {date_str}")
    except Exception as e:
        _rlog(f"context_brief: cache bust error: {e}")


def _save_brief_cache(script_dir, date_str, en, hi):
    """Write EN+HI briefs to cache, pruning entries older than 7 days."""
    path = _brief_cache_path(script_dir)
    try:
        try:
            with open(path, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cache = {}
        existing = cache.get(date_str, {})
        if existing.get("en") == en and existing.get("hi") == hi:
            return  # already cached — no write needed
        cutoff = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        cache = {k: v for k, v in cache.items() if k >= cutoff}
        cache[date_str] = {
            "en": en, "hi": hi,
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds")
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        _rlog(f"context_brief: cached for {date_str}")
    except Exception as e:
        _rlog(f"context_brief: cache save error: {e}")


def _build_brief_base(notes_block, n):
    """Shared base prompt for brief generation."""
    return (
        f"Here are the last {n} day(s) of evening journal entries:\n\n"
        f"{notes_block}"
        "Write a 3-4 sentence synthesis: what patterns do you see, "
        "what was recurring or unfinished, and one forward-looking nudge for today. "
        "Be specific and concise. No bullet points."
    )


def _parse_ollama_text(response, utils):
    """Extract clean text from an Ollama response dict."""
    if isinstance(response, dict) and not response.get("error"):
        return utils.clean_response(response.get("response", "").strip())
    if not isinstance(response, dict):
        return str(response).strip()
    return ""


def _call_brief_single(notes_block, n, host, model, temp):
    """One Ollama call → returns (en_text, hi_text) using EN:/HI: block format."""
    import utils as _utils
    prompt = (
        _build_brief_base(notes_block, n) + "\n\n"
        "Return your response in EXACTLY this format (no other text):\n"
        "EN: <English synthesis>\n"
        "HI: <Same synthesis in natural Hindi>"
    )
    raw = _parse_ollama_text(_utils.call_ollama(host, model, prompt, [], temp), _utils)
    en, hi = "", ""
    for line in raw.splitlines():
        if line.startswith("EN:"):
            en = line[3:].strip()
        elif line.startswith("HI:"):
            hi = line[3:].strip()
    # Fallback: model didn't follow format — use full response for both
    return en or raw, hi or raw


def _call_brief_parallel(notes_block, n, host, model_en, model_hi, temp):
    """Two parallel Ollama calls — one per language. Returns (en_text, hi_text)."""
    import utils as _utils
    import queue as _q

    base = _build_brief_base(notes_block, n)
    prompt_en = base + "\n\nWrite in English only."
    prompt_hi = base + "\n\nWrite in natural Hindi only."
    out = _q.Queue()

    def _call(lang, model, prompt):
        try:
            text = _parse_ollama_text(_utils.call_ollama(host, model, prompt, [], temp), _utils)
        except Exception as e:
            _rlog(f"context_brief/{lang}: error: {e}")
            text = ""
        out.put((lang, text))

    t_en = threading.Thread(target=_call, args=("en", model_en, prompt_en), daemon=True)
    t_hi = threading.Thread(target=_call, args=("hi", model_hi, prompt_hi), daemon=True)
    t_en.start(); t_hi.start()
    t_en.join(); t_hi.join()
    results = dict(out.get() for _ in range(2))
    return results.get("en", ""), results.get("hi", "")


def _run_context_brief(script_dir, config, state):
    """Background thread: synthesise last N days (EN+HI), cache, narrate, then prompt Step 1."""
    import utils as _utils
    n = config.get("last_n_days_context", 3)
    date_str = state.get("date") or datetime.date.today().isoformat()
    _rlog(f"context_brief: reading last {n} days before {date_str}")

    notes_data = _read_last_n_notes(script_dir, config, n, date_str)
    fallback_en = f"No evening review notes found for the last {n} day{'s' if n != 1 else ''}."
    fallback_hi = f"पिछले {n} दिनों की कोई समीक्षा नहीं मिली।"

    if not notes_data:
        brief_en, brief_hi = fallback_en, fallback_hi
        _rlog("context_brief: no notes found")
    else:
        # Check cache first
        cached = _load_brief_cache(script_dir, date_str)
        if cached:
            brief_en = cached["en"]
            brief_hi = cached["hi"]
        else:
            notes_block = ""
            for note in reversed(notes_data):
                notes_block += f"--- {note['date']} ---\n{note['content']}\n\n"
            try:
                main_config = _utils.load_config(script_dir)
                host  = config.get("ollama_host") or main_config.get("OLLAMA_HOST", "http://localhost:11434")
                temp  = main_config.get("TEMPERATURE", 0.3)
                default_model = config.get("structure_model") or main_config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")

                model_en = config.get("brief_model_en") or config.get("brief_model") or default_model
                model_hi = config.get("brief_model_hi") or config.get("brief_model") or default_model

                if model_en == model_hi:
                    brief_en, brief_hi = _call_brief_single(notes_block, n, host, model_en, temp)
                    _rlog(f"context_brief: single-model generation done (model={model_en})")
                else:
                    brief_en, brief_hi = _call_brief_parallel(notes_block, n, host, model_en, model_hi, temp)
                    _rlog(f"context_brief: parallel generation done (en={model_en}, hi={model_hi})")

                # Only cache real synthesis — never cache fallback/error text.
                # An empty response means the model was busy or returned nothing;
                # next session should retry rather than serve a stale "unavailable" message.
                if brief_en and brief_hi:
                    _save_brief_cache(script_dir, date_str, brief_en, brief_hi)
                else:
                    _rlog("context_brief: model returned empty — not caching, will retry next session")

                if not brief_en:
                    brief_en = f"Notes loaded for {len(notes_data)} day(s). AI synthesis unavailable."
                if not brief_hi:
                    brief_hi = f"{len(notes_data)} दिनों के नोट्स लोड हुए। AI synthesis उपलब्ध नहीं।"
            except Exception as e:
                _rlog(f"context_brief: exception: {e}")
                brief_en = f"Notes loaded for {len(notes_data)} day(s). Could not generate synthesis."
                brief_hi = f"{len(notes_data)} दिनों के नोट्स लोड हुए। synthesis नहीं हो सकी।"

    # Pick language for narration and display
    lang = config.get("context_brief_language", "en")
    brief = brief_hi if lang == "hi" else brief_en

    # Write back to live state file
    live_state = load_state()
    if live_state:
        live_state["context_brief"]    = brief
        live_state["context_brief_en"] = brief_en
        live_state["context_brief_hi"] = brief_hi
        live_state["context_ready"]    = True
        live_state["context_notes"]    = notes_data
        _save_state(live_state)
        _rlog("context_brief: state updated with context_ready=True")
        if notes_data:
            narrate(brief, config, blocking=True)

        # Narrate weekly focus word trend on Sundays (blocking)
        if config.get("focus_word_trend", True):
            review_date = datetime.date.fromisoformat(date_str)
            if review_date.weekday() == 6:   # Sunday
                word, count = _get_weekly_focus_trend(script_dir)
                if word and count >= 2:
                    trend_text = f"इस हफ्ते आपका सबसे ज़्यादा ध्यान '{word}' पर रहा।"
                    narrate(trend_text, config, blocking=True)
                    _rlog(f"focus_word: Sunday trend narrated: '{word}' (×{count})")

        send_step_notification(live_state, config)
    else:
        _rlog("context_brief: state gone before brief was ready — skipping narration")


def regenerate_brief(script_dir, config):
    """Bust today's brief cache and regenerate asynchronously.

    Clears the cached brief from state, saves state, then spawns a background
    thread to regenerate and narrate the brief. Safe to call from any process.
    `_save_state` and `_run_context_brief` stay private — callers use this wrapper.
    """
    state = load_state()
    if state is None:
        _rlog("regenerate_brief: no active state, nothing to regenerate")
        return
    date_str = state.get("date") or datetime.date.today().isoformat()
    _bust_brief_cache(script_dir, date_str)
    state.pop("context_brief", None)
    state.pop("context_brief_en", None)
    state.pop("context_brief_hi", None)
    state["context_ready"] = False
    _save_state(state)
    _rlog(f"regenerate_brief: cache busted, spawning background thread for {date_str}")
    threading.Thread(
        target=_run_context_brief,
        args=(script_dir, config, dict(state)),
        daemon=True
    ).start()


def _fill_section(file_path, section_name, text):
    """Find ### section_name in file and insert text below it.
    If the section already has content, appends after existing content.
    If section not found, appends at end of file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    header_match = re.search(r'^### ' + re.escape(section_name) + r'\s*$', content, re.MULTILINE)
    if header_match is None:
        # Section header not found — append at end
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n### {section_name}\n{text}\n")
        _rlog(f"_fill_section: '{section_name}' header not found, appended at end")
        return

    # Find line after the header
    after_header_pos = content.find("\n", header_match.start())
    if after_header_pos == -1:
        after_header_pos = len(content)
    after_header_pos += 1  # move past the newline

    # Find next section header (## or ###) to know where this section ends
    next_section_match = re.search(r'\n#{2,3} ', content[after_header_pos:])
    if next_section_match:
        section_end = after_header_pos + next_section_match.start() + 1  # +1 for \n
    else:
        section_end = len(content)

    # Check existing content in section
    existing = content[after_header_pos:section_end].strip()
    if existing:
        # Has content — insert after existing, before next section
        insert = f"\n{text}\n"
        new_content = content[:section_end] + insert + content[section_end:]
    else:
        # Empty section — insert directly after header
        insert = f"{text}\n"
        new_content = content[:after_header_pos] + insert + content[after_header_pos:]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    _rlog(f"_fill_section: wrote '{section_name}' into existing section")


# ── Streak helpers ────────────────────────────────────────────────────────────

_STREAK_MILESTONES = {7: "एक हफ्ता", 14: "दो हफ्ते", 30: "एक महीना", 100: "सौ दिन"}


def _streak_path(script_dir):
    return os.path.join(script_dir, "streak.json")


def load_streak(script_dir):
    try:
        with open(_streak_path(script_dir), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"current": 0, "last_date": "", "best": 0}


def _save_streak(script_dir, streak):
    try:
        with open(_streak_path(script_dir), "w", encoding="utf-8") as f:
            json.dump(streak, f, ensure_ascii=False, indent=2)
        _rlog(f"streak: saved current={streak['current']}, best={streak['best']}")
    except Exception as e:
        _rlog(f"streak: save error: {e}")


def update_streak(script_dir, date_str):
    """Increment streak for date_str (called at review completion). Returns updated dict."""
    streak = load_streak(script_dir)
    last_date = streak.get("last_date", "")
    current   = streak.get("current", 0)
    best      = streak.get("best", 0)

    if last_date == date_str:
        return streak   # already recorded today — no double-count

    yesterday = (datetime.date.fromisoformat(date_str) - datetime.timedelta(days=1)).isoformat()
    current = current + 1 if (last_date == yesterday or not last_date) else 1
    best    = max(best, current)
    updated = {"current": current, "last_date": date_str, "best": best}
    _save_streak(script_dir, updated)
    return updated


# ── Focus word trend helpers ──────────────────────────────────────────────────

def _focus_words_path(script_dir):
    return os.path.join(script_dir, "focus_words.jsonl")


def _append_focus_word(script_dir, date_str, word):
    """Append {date, word} as a JSON line to focus_words.jsonl."""
    word = word.strip()
    if not word:
        return
    try:
        with open(_focus_words_path(script_dir), "a", encoding="utf-8") as f:
            f.write(json.dumps({"date": date_str, "word": word}, ensure_ascii=False) + "\n")
        _rlog(f"focus_word: appended '{word}' for {date_str}")
    except Exception as e:
        _rlog(f"focus_word: append error: {e}")


def _read_focus_words(script_dir, n):
    """Return the last n valid entries from focus_words.jsonl as a list of dicts.
    Reads only the tail of the file to avoid loading unbounded history into memory.
    Returns empty list if the file is missing or unreadable."""
    path = _focus_words_path(script_dir)
    buf = collections.deque(maxlen=n)
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        buf.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        return []
    except Exception as e:
        _rlog(f"focus_word: read error: {e}")
        return []
    return list(buf)


def _get_weekly_focus_trend(script_dir):
    """Return (most_common_word, count) from the last 7 focus_words.jsonl entries.
    Returns (None, 0) if the file is missing or has fewer than 2 entries."""
    if len(_read_focus_words(script_dir, 7)) < 2:
        return None, 0
    ranked = get_focus_word_counts(script_dir, n=7)
    if not ranked:
        return None, 0
    return ranked[0]


def get_focus_word_counts(script_dir, n=7):
    """Return sorted [(word, count)] from the last n focus_words.jsonl entries.
    Returns empty list if the file is missing or has no valid entries."""
    entries = _read_focus_words(script_dir, n)
    counts = collections.Counter(e["word"].lower() for e in entries if e.get("word"))
    return counts.most_common()


# ── Carry-forward task helpers ────────────────────────────────────────────────

def _read_unchecked_tasks(script_dir, config, date_str):
    """Return list of unchecked task strings from the day-before date_str's daily note."""
    prev_date = (datetime.date.fromisoformat(date_str) - datetime.timedelta(days=1)).isoformat()
    note_path = get_daily_note_path(script_dir, config, prev_date)
    tasks = []
    try:
        with open(note_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("- [ ]"):
                    task_text = stripped[5:].strip()
                    if task_text:
                        tasks.append(task_text)
    except FileNotFoundError:
        pass
    except Exception as e:
        _rlog(f"_read_unchecked_tasks: error reading {note_path}: {e}")
    _rlog(f"_read_unchecked_tasks: found {len(tasks)} tasks from {prev_date}")
    return tasks


def mark_task_done(script_dir, config, task_text, note_date_str):
    """Replace '- [ ] task_text' with '- [x] task_text' in note_date_str's daily note.
    Returns True on success, False if the line was not found or an error occurred."""
    note_path = get_daily_note_path(script_dir, config, note_date_str)
    old_line = f"- [ ] {task_text}"
    new_line = f"- [x] {task_text}"
    try:
        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()
        if old_line not in content:
            _rlog(f"_mark_task_done: line not found in {note_path}: {task_text!r}")
            return False
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content.replace(old_line, new_line, 1))
        _rlog(f"_mark_task_done: marked done in {note_path}: {task_text!r}")
        return True
    except Exception as e:
        _rlog(f"_mark_task_done: error: {e}")
        return False


# ── Core review functions ─────────────────────────────────────────────────────

def initialize_review(script_dir, date_str=None):
    """Initialise a new review session.

    date_str: YYYY-MM-DD string for the note date. Defaults to today.
              Use this to backfill a review for a past date.
    """
    init_logging(script_dir)
    _rlog("=" * 50)
    _rlog("initialize_review called")

    # Defensive guard: refuse to overwrite a live session.
    # start_review() in tray_app already has a re-entry guard, but this protects
    # against any future caller that bypasses it.
    active, _ = is_review_active(script_dir)
    if active:
        _rlog("initialize_review: review already active — aborting to prevent state overwrite")
        return

    config = load_review_config(script_dir)

    # Resolve the note date (may differ from today for past-date reviews)
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    try:
        note_date = datetime.date.fromisoformat(date_str)
    except ValueError:
        _rlog(f"initialize_review: invalid date_str '{date_str}', falling back to today")
        note_date = datetime.date.today()
        date_str = note_date.isoformat()

    vault_paths = config.get("vault_paths", {})
    daily_notes_base = os.path.expanduser(vault_paths.get("daily_notes", "~/learning_vault/My Daily Notes"))
    wellness_base = os.path.expanduser(vault_paths.get("wellness_notes", "~/learning_vault/My Daily Notes/Wellness"))

    # Pre-create the note date's year/month directories
    year, month = note_date.strftime("%Y"), note_date.strftime("%B")
    try:
        os.makedirs(os.path.join(daily_notes_base, year, month), exist_ok=True)
        os.makedirs(os.path.join(wellness_base, year, month), exist_ok=True)
        _rlog(f"Vault directories ensured for {date_str}")
    except Exception as e:
        _rlog(f"ERROR creating vault dirs: {e}")

    now = datetime.datetime.now()
    state = {
        "active": True,
        "current_step_index": 0,
        "date": date_str,           # the note date (may be any date)
        "started_at": now.isoformat(),  # always now — used for expiry/staleness checks
        "last_written": None,
        "awaiting_more": False,
        "accumulated_raw": [],
        "interview_raw": {},         # step_id → combined raw text, filled during interview
        "step_started_at": now.isoformat(),  # timer for per-step duration tracking
        "step_times": [],                    # seconds per step, appended at each advance/skip/complete
    }
    n = config.get("last_n_days_context", 3)
    if n and n > 0:
        # Context brief runs async; it narrates then calls send_step_notification for Step 1
        state["context_brief"] = None
        state["context_ready"] = False
        state["context_notes"] = []
    else:
        state["context_brief"] = ""
        state["context_ready"] = True
        state["context_notes"] = []

    # Carry-forward: scan last N days for unchecked tasks (multi-day, age-aware)
    if config.get("carryforward_tasks", False):
        prev_date = (datetime.date.fromisoformat(date_str) - datetime.timedelta(days=1)).isoformat()
        state["carryforward_tasks"] = get_pending_tasks(script_dir, config)
        state["carryforward_date"] = prev_date
    else:
        state["carryforward_tasks"] = []
        state["carryforward_date"] = ""

    # Streak: load current count so dashboard can display it from the start
    if config.get("show_streak", True):
        streak = load_streak(script_dir)
        state["streak_current"] = streak.get("current", 0)
    else:
        state["streak_current"] = 0

    _save_state(state)
    _rlog(f"Review initialized for {date_str}. Steps: {len(config.get('review_steps', []))}. context_n={n}")

    if n and n > 0:
        threading.Thread(target=_run_context_brief, args=(script_dir, config, dict(state)), daemon=True).start()
    else:
        send_step_notification(state, config)


def get_current_step(state, config):
    steps = config.get("review_steps", [])
    idx = state.get("current_step_index", 0)
    if 0 <= idx < len(steps):
        return steps[idx]
    return None


def get_step_count(config):
    return len(config.get("review_steps", []))


def write_step_to_note(script_dir, config, step, structured_text, state):
    """Write structured text to the correct note file.
    - section_fill=True: find existing ### section and fill it in
    - section_fill=False: append below ## Evening Review
    """
    # Use the review session's own date (not today) so after-midnight sessions
    # still write to the correct note file.
    date_str = state.get("date") or datetime.date.today().isoformat()
    section_name = step.get("section_name", "Note")
    is_isolated = step.get("isolate_file", False)

    if is_isolated:
        file_path = _get_wellness_note_path(script_dir, config, date_str)
    else:
        file_path = get_daily_note_path(script_dir, config, date_str)

    _rlog(f"write_step_to_note: step='{section_name}' file='{file_path}'")

    write_offset = None  # byte position before our write — used by redo_step to truncate
    try:
        # Create file with the correct template if it doesn't exist
        if not os.path.exists(file_path):
            if is_isolated:
                _create_wellness_note(file_path, date_str)
            else:
                _create_daily_note(file_path, date_str)

        if is_isolated:
            # Isolated files (e.g. Wellness): just append raw text, no section scaffolding
            block = f"### {section_name}\n{structured_text}\n"
            with open(file_path, "a", encoding="utf-8") as f:
                write_offset = f.seek(0, 2)  # atomic: offset captured inside the open
                f.write(block)
            _rlog(f"write_step_to_note: appended {len(block)} chars to isolated file")
        elif step.get("section_fill", False):
            # In-place fill — offset tracking not supported; redo will notify user manually
            _fill_section(file_path, section_name, structured_text)
        else:
            _ensure_evening_review_section(file_path)
            block = f"### {section_name}\n{structured_text}\n"
            with open(file_path, "a", encoding="utf-8") as f:
                write_offset = f.seek(0, 2)  # atomic: offset captured inside the open
                f.write(block)
            _rlog(f"write_step_to_note: appended {len(block)} chars under Evening Review")

    except Exception as e:
        _rlog(f"ERROR in write_step_to_note: {e}")
        return

    state["last_written"] = {"file": file_path, "section": section_name, "offset": write_offset}
    _save_state(state)

    # Track focus word for weekly trend (Focus Word section only, non-isolated)
    if (section_name == "Focus Word"
            and not is_isolated
            and config.get("focus_word_trend", True)):
        _append_focus_word(script_dir, date_str, structured_text.strip())


def fmt_duration(t):
    """Format integer seconds as '2m 05s' or '47s'."""
    m, s = divmod(t, 60)
    return f"{m}m {s:02d}s" if m else f"{s}s"


def _record_step_time(state):
    """Append elapsed seconds for the current step to step_times and reset the timer."""
    now = datetime.datetime.now()
    started = state.get("step_started_at")
    if started:
        try:
            elapsed = int((now - datetime.datetime.fromisoformat(started)).total_seconds())
            state.setdefault("step_times", []).append(elapsed)
        except ValueError as e:
            _rlog(f"_record_step_time: could not parse step_started_at: {e}")
    state["step_started_at"] = now.isoformat()


def _clear_step_accumulation(state):
    """Reset per-step accumulation fields after a step is written, skipped, or redone."""
    state["last_written"]    = None
    state["awaiting_more"]   = False
    state["accumulated_raw"] = []


def advance_step(script_dir, state, config):
    steps = config.get("review_steps", [])
    prev = state.get("current_step_index", 0)
    _record_step_time(state)
    state["current_step_index"] = prev + 1
    _clear_step_accumulation(state)
    _rlog(f"advance_step: {prev} → {state['current_step_index']} (total={len(steps)})")

    if state["current_step_index"] >= len(steps):
        _rlog("advance_step: last step done, calling complete_review")
        complete_review(script_dir, None, state, config)
    else:
        _save_state(state)
        send_step_notification(state, config)


def skip_step(script_dir, state, config):
    steps = config.get("review_steps", [])
    prev = state.get("current_step_index", 0)
    current_step = steps[prev] if prev < len(steps) else {}

    # Write skip_default to the note before advancing (e.g. Movement → "only office")
    skip_default = current_step.get("skip_default", "").strip()
    if skip_default:
        _rlog(f"skip_step: writing skip_default '{skip_default}' for step '{current_step.get('section_name')}'")
        write_step_to_note(script_dir, config, current_step, skip_default, state)

    _record_step_time(state)
    state["current_step_index"] = prev + 1
    _clear_step_accumulation(state)
    _rlog(f"skip_step: {prev} → {state['current_step_index']} (total={len(steps)})")

    if state["current_step_index"] >= len(steps):
        _rlog("skip_step: last step skipped, calling complete_review")
        complete_review(script_dir, None, state, config)
    else:
        narrate(_ui_narration("step_skipped", config), config, blocking=True)
        _save_state(state)
        send_step_notification(state, config)


def redo_step(script_dir, state, config):
    """Reset the current step for re-recording, removing previously written content from the note."""
    last_written = state.get("last_written")
    if last_written:
        section_name = last_written.get("section", "this step")
        file_path    = last_written.get("file", "")
        offset       = last_written.get("offset")  # None for section_fill steps

        if file_path and offset is not None:
            # Truncate the file back to the pre-write position — fully reversible
            try:
                with open(file_path, "r+b") as f:
                    f.truncate(offset)
                _rlog(f"redo_step: truncated '{file_path}' back to offset {offset} (removed '{section_name}')")
            except Exception as e:
                _rlog(f"redo_step: truncate failed for '{file_path}': {e}")
                send_notification(
                    "Evening Review — Redo",
                    f"Could not auto-remove '{section_name}' from note — please remove it manually."
                )
        elif file_path:
            # section_fill step — in-place edit, cannot be simply truncated
            _rlog(f"redo_step: section_fill step '{section_name}' — notifying user to clean up manually")
            send_notification(
                "Evening Review — Redo",
                f"'{section_name}' was filled in-place — remove its content from the note manually. Re-recording now."
            )

    _clear_step_accumulation(state)
    _save_state(state)
    _rlog("redo_step: state cleared, re-prompting step")
    send_step_notification(state, config)


def accumulate_clip(state, raw_text):
    """Append a raw transcription clip to the current step's accumulation buffer.

    Saves state to disk and returns the updated state dict.
    Called by tray_app after each successful recording during a review step.
    """
    state.setdefault("accumulated_raw", []).append(raw_text)
    state["awaiting_more"] = True
    _save_state(state)
    _rlog(f"accumulate_clip: clip {len(state['accumulated_raw'])} appended ({len(raw_text)} chars)")
    return state


def structure_and_advance(script_dir, engine_instance, config):
    """Acquire exclusive processing lock, LLM-structure accumulated clips, write to note, advance step.

    Returns ``(success, error, still_active)`` where:
    - success      – False if the lock is held by another process or state is gone; True otherwise
    - error        – exception message string if something failed mid-run, else None
    - still_active – True if the review session is still running after this call

    Locking strategy
    ----------------
    An exclusive file lock on ``_PROCESSING_LOCK_PATH`` (non-blocking) is the atomic gate.
    If another process holds the lock, this function returns immediately without blocking.
    ``state["processing"]`` is kept only as a display signal for the dashboard spinner;
    it no longer does any locking itself.

    ``skip_step`` is called internally when no raw text is accumulated.  It must NOT try to
    acquire the same lock — flock(LOCK_EX) from the same process via a second open() would
    deadlock.  ``skip_step`` relies on the callers' state.get("processing") pre-checks instead.
    """
    import traceback as _tb
    _lock_fd      = None
    _processing_set = False   # True once state["processing"]=True has been saved (for finally cleanup)
    try:
        # ── Step 1: Acquire exclusive lock (atomic, non-blocking) ────────────────
        _lock_fd = _acquire_processing_lock()
        if _lock_fd is None:
            _rlog("structure_and_advance: processing lock held by another process — bailing")
            return False, None, True  # still_active unknown; don't kill review

        # ── Step 2: Load state and set display flag ──────────────────────────────
        fresh_state = load_state()
        if fresh_state is None:
            _rlog("structure_and_advance: state file gone before processing started")
            return False, None, False

        fresh_state["processing"] = True
        _save_state(fresh_state)
        _processing_set = True
        state = fresh_state

        # ── Step 3: Structure and advance ────────────────────────────────────────
        step = get_current_step(state, config)
        if step is None:
            _rlog("structure_and_advance: no step found")
            return True, None, False

        step_name    = step.get("section_name", "this step")
        raw_list     = state.get("accumulated_raw", [])
        raw_combined = "\n".join(raw_list).strip()

        if not raw_combined:
            _rlog("structure_and_advance: no accumulated raw, treating as skip")
            skip_step(script_dir, state, config)
        else:
            if step.get("isolate_file", False):
                # Wellness and other isolated steps: write immediately to their own file.
                # refine=False for these so use raw text directly.
                _rlog(f"structure_and_advance: isolated step '{step_name}' — writing immediately")
                if engine_instance is not None:
                    engine_instance.log(raw_combined, raw_combined,
                                        mode=f"review:{step_name}", model="review_engine")
                state["accumulated_raw"] = []
                state["awaiting_more"]   = False
                write_step_to_note(script_dir, config, step, raw_combined, state)
                # Log isolated steps to review_log.json as both raw and structured
                # (they are written verbatim — no secretary LLM involved)
                _log_review(script_dir, {
                    "session_date":    state.get("date", ""),
                    "step_id":         step.get("step_id", ""),
                    "step_name":       step_name,
                    "event":           "step_structured",
                    "raw_text":        raw_combined,
                    "structured_text": raw_combined,
                    "note":            "isolated step — written verbatim",
                })
            else:
                # Secretary model: accumulate raw interview text — LLM synthesis runs after
                # the final step in _secretary_synthesis() called from complete_review().
                _rlog(f"structure_and_advance: storing '{step_name}' in interview_raw ({len(raw_list)} clips)")
                step_id = str(step.get("step_id", step_name))
                state.setdefault("interview_raw", {})[step_id] = raw_combined
                state["accumulated_raw"] = []
                state["awaiting_more"]   = False

            advance_step(script_dir, state, config)

        still_active, _ = is_review_active(script_dir)
        return True, None, still_active

    except Exception as e:
        _rlog(f"EXCEPTION in structure_and_advance:\n{_tb.format_exc()}")
        # success=False signals the caller that processing failed.
        # still_active=True keeps the review alive so the user can retry.
        return False, str(e), True
    finally:
        # Clear the display flag from state (if we set it), then release the file lock.
        if _processing_set:
            final_state = load_state()
            if final_state is not None:
                final_state.pop("processing", None)
                _save_state(final_state)
        _release_processing_lock(_lock_fd)


def cancel_review(script_dir):
    _rlog("cancel_review called")
    config = load_review_config(script_dir)
    try:
        if os.path.exists(STATE_PATH):
            os.remove(STATE_PATH)
            _rlog("State file deleted")
    except Exception as e:
        _rlog(f"ERROR deleting state file: {e}")
    narrate(_ui_narration("review_cancelled", config), config)
    send_notification("Evening Review", "Review cancelled. Returning to normal mode.")


def _generate_and_append_summary(script_dir, daily_note_path, date_str):
    """Background thread: generates an AI summary and appends it to the daily note."""
    _rlog("_generate_and_append_summary: starting")
    try:
        if not os.path.exists(daily_note_path):
            _rlog("_generate_and_append_summary: daily note not found, skipping")
            return
        with open(daily_note_path, "r", encoding="utf-8") as f:
            note_content = f.read()
        if not note_content.strip():
            _rlog("_generate_and_append_summary: daily note empty, skipping")
            return

        import utils
        main_config = utils.load_config(script_dir)
        host = main_config.get("OLLAMA_HOST", "http://localhost:11434")
        models = main_config.get("OLLAMA_MODELS", {})
        model = models.get("en", "qwen2.5:3b")
        prompt = f"In 2-3 sentences, summarize this daily review entry:\n\n{note_content}"
        response = utils.call_ollama(host, model, prompt, [], main_config.get("TEMPERATURE", 0.1))
        if "error" in response:
            _rlog(f"_generate_and_append_summary: Ollama error: {response['error']}")
            return

        summary = utils.clean_response(response.get("response", "")).strip()
        if not summary:
            return

        summary_block = f"\n### \U0001f4cb Daily Summary\n{summary}\n"
        with open(daily_note_path, "a", encoding="utf-8") as f:
            f.write(summary_block)
        _rlog(f"_generate_and_append_summary: summary appended ({len(summary)} chars)")
        send_notification("Evening Review", "AI summary added to your daily note.")
    except Exception as e:
        _rlog(f"_generate_and_append_summary: ERROR: {e}")


def _secretary_synthesis(script_dir, config, state, daily_note_path):
    """One LLM call that reads all raw interview answers and writes each note section.

    The 'secretary' sees the full interview context at once, so it can:
    - Route meeting details mentioned in Movement into ### Meeting
    - Pull action items from any answer into ### Tomorrow's Priorities
    - Avoid duplication across sections

    Isolated steps (Wellness) are excluded — they are written immediately during the
    interview.  Skipped steps are excluded — they write their skip_default immediately
    via skip_step().  Only steps with recorded content in interview_raw are processed.
    """
    steps = config.get("review_steps", [])
    interview_raw = state.get("interview_raw", {})

    # Build per-step lines for the transcript, preserving conversation order
    transcript_lines = []
    recorded_sections = []
    for step in steps:
        if step.get("isolate_file", False):
            continue
        step_id  = str(step.get("step_id", step.get("section_name", "")))
        raw      = interview_raw.get(step_id, "").strip()
        if not raw:
            continue  # skipped step — already written via skip_step()
        section  = step.get("section_name", "")
        question = step.get("prompt_notification", f"Tell me about {section}.")
        # Strip "Step N/6: " prefix from prompt_notification for cleaner display
        question = re.sub(r'^Step \d+/\d+:\s*', '', question)
        transcript_lines.append(f"[{section}]\nQ: {question}\nA: {raw}")
        recorded_sections.append(section)

    if not transcript_lines:
        _rlog("_secretary_synthesis: no recorded interview data — nothing to synthesise")
        return

    transcript = "\n\n".join(transcript_lines)

    # Build the output template listing only the sections that need to be filled.
    # Sections already filled by skip_default are NOT listed here.
    section_formats = {
        "Movement":             "[1–2 plain sentences about physical movement/location.]",
        "Meeting":              "[Per meeting: **Meeting:** <title>\\n- Time: / Place: / Attendees: / Chairperson: / Discussion: / Decisions: •]",
        "Achievements":         "[Numbered paragraphs: 1. First achievement…  2. Second…]",
        "Tomorrow's Priorities":"[Checkbox list: - [ ] task. Include action items from ALL sections.]",
        "Focus Word":           "[Single word or short phrase only.]",
    }
    output_blocks = "\n\n".join(
        f"### {s}\n{section_formats.get(s, '[content]')}"
        for s in recorded_sections
    )

    prompt = (
        "You are an executive secretary writing a professional's daily review notes "
        "from a voice interview transcript.\n\n"
        "Read carefully. Some answers may contain information relevant to OTHER sections:\n"
        "- Movement answers may mention meetings → extract into ### Meeting\n"
        "- Any answer may mention tasks for tomorrow → add to ### Tomorrow's Priorities\n"
        "- Do not duplicate content across sections\n"
        "- Write concisely and professionally\n"
        "- If a section has no relevant information, write a single dash (-)\n"
        "- Output ONLY the section blocks shown below, nothing else\n\n"
        f"INTERVIEW TRANSCRIPT:\n{transcript}\n\n"
        f"OUTPUT:\n{output_blocks}"
    )

    host  = config.get("ollama_host", "http://localhost:11434")
    # Prefer a dedicated secretary_model (qwen2.5:3b works well for English-structured
    # output); fall back to the general structure_model if not set.
    model = config.get("secretary_model") or config.get("structure_model", "")

    def _fallback_write():
        """If LLM synthesis fails, write raw interview text directly under each section."""
        _rlog("_secretary_synthesis: using raw-text fallback")
        send_notification("Daily Review — Note", "AI organisation failed — raw notes saved.")
        for step in steps:
            if step.get("isolate_file", False):
                continue
            step_id  = str(step.get("step_id", step.get("section_name", "")))
            raw      = interview_raw.get(step_id, "").strip()
            section  = step.get("section_name", "")
            if raw and section:
                try:
                    _fill_section(daily_note_path, section, raw)
                except Exception as fe:
                    _rlog(f"_secretary_synthesis fallback: error writing '{section}': {fe}")

    if not model:
        _rlog("_secretary_synthesis: no model configured — skipping")
        _fallback_write()
        return

    _rlog(f"_secretary_synthesis: calling '{model}' with {len(recorded_sections)} sections")
    try:
        result = _utils.call_ollama(host, model, prompt, stop_tokens=[], temperature=0.2, timeout=300)
    except Exception as e:
        _rlog(f"_secretary_synthesis: LLM call failed: {e}")
        _fallback_write()
        return

    # call_ollama returns a dict {"response": "...", ...} or {"error": "..."}
    if isinstance(result, dict):
        if "error" in result:
            _rlog(f"_secretary_synthesis: model error: {result['error']}")
            _fallback_write()
            return
        raw_response = result.get("response", "")
    else:
        raw_response = str(result)

    raw_response = raw_response.strip()
    if not raw_response:
        _rlog("_secretary_synthesis: empty response from model")
        _fallback_write()
        return

    _rlog(f"_secretary_synthesis: response ({len(raw_response)} chars), preview='{raw_response[:120]}'")

    # Parse response: split on ### headers
    parts = re.split(r'^### (.+)$', raw_response, flags=re.MULTILINE)
    # parts = [preamble, section_name, content, section_name, content, ...]
    i = 1
    while i + 1 < len(parts):
        section_name = parts[i].strip()
        content      = parts[i + 1].strip()
        i += 2
        if not content or content == "-":
            _rlog(f"_secretary_synthesis: no content for '{section_name}', skipping")
            continue
        _rlog(f"_secretary_synthesis: writing '{section_name}' ({len(content)} chars)")
        try:
            _fill_section(daily_note_path, section_name, content)
        except Exception as e:
            _rlog(f"_secretary_synthesis: error writing '{section_name}': {e}")

        # Log structured output to review_log.json (raw_text comes from interview_raw)
        matched_step = next(
            (s for s in steps if s.get("section_name", "").lower() == section_name.lower()),
            None,
        )
        raw_for_step = ""
        if matched_step:
            raw_for_step = interview_raw.get(str(matched_step.get("step_id", "")), "")
        _log_review(script_dir, {
            "session_date":    state.get("date", ""),
            "step_id":         matched_step.get("step_id", "") if matched_step else "",
            "step_name":       section_name,
            "event":           "step_structured",
            "raw_text":        raw_for_step,
            "structured_text": content,
        })

        # Track focus word separately (stored in jsonl for trend)
        if section_name == "Focus Word" and config.get("focus_word_trend", True):
            date_str = state.get("date", datetime.date.today().isoformat())
            _append_focus_word(script_dir, date_str, content)


def complete_review(script_dir, engine_instance, state, config):
    date_str = state.get("date", datetime.date.today().isoformat())
    daily_note_path = get_daily_note_path(script_dir, config, date_str)

    _rlog(f"complete_review: date={date_str} daily_note={daily_note_path}")

    # Ensure daily note exists before synthesis writes to it
    if not os.path.exists(daily_note_path):
        try:
            _create_daily_note(daily_note_path, date_str)
            _rlog(f"complete_review: created daily note at {daily_note_path}")
        except Exception as e:
            _rlog(f"complete_review: ERROR creating daily note: {e}")

    # Secretary synthesis: one LLM call organises all interview_raw into note sections.
    # Must run BEFORE state is deleted (needs interview_raw).
    # Set synthesising=True so the dashboard shows a locked spinner during this phase.
    state["synthesising"] = True
    _save_state(state)
    send_notification("Daily Review — Writing Notes", "Secretary is organising your notes…")
    _secretary_synthesis(script_dir, config, state, daily_note_path)

    # Update streak before deleting state so the dashboard's final poll tick
    # can display the newly-incremented value before _show_complete() fires.
    if config.get("show_streak", True):
        updated = update_streak(script_dir, date_str)
        new_n = updated.get("current", 0)
        state["streak_current"] = new_n
        _save_state(state)   # brief write so dashboard picks up step_times + streak
    else:
        new_n = 0

    # Delete state so review is no longer active
    try:
        if os.path.exists(STATE_PATH):
            os.remove(STATE_PATH)
            _rlog("complete_review: state file deleted")
    except Exception as e:
        _rlog(f"complete_review: ERROR deleting state file: {e}")

    narrate(_ui_narration("review_complete", config), config)

    # Narrate milestone if applicable
    if new_n in _STREAK_MILESTONES:
        milestone_text = f"वाह! {_STREAK_MILESTONES[new_n]} लगातार समीक्षा के! बहुत शानदार!"
        narrate(milestone_text, config)

    send_notification("Evening Review Complete", "Notes written to your vault. Great work!")
    streak_n = state.get("streak_current", 0)
    streak_str = f"🔥 Streak: {streak_n} day{'s' if streak_n != 1 else ''}\n" if streak_n > 0 else ""
    send_telegram(
        f"✅ Evening Review done for {date_str}\n{streak_str}Great work!",
        config
    )

    if config.get("generate_daily_summary", False):
        t = threading.Thread(
            target=_generate_and_append_summary,
            args=(script_dir, daily_note_path, date_str),
            daemon=True
        )
        t.start()
        _rlog("complete_review: background summary thread started")
    else:
        _rlog("complete_review: generate_daily_summary=false, skipping summary")


def check_startup_state(script_dir):
    config = load_review_config(script_dir)
    state = load_state()

    if state is None:
        return "none", None, None

    # Expire if the SESSION (started_at) is from a previous day, not the note date.
    try:
        started_date = datetime.datetime.fromisoformat(state["started_at"]).date().isoformat()
    except Exception:
        started_date = state.get("date", "")
    today = datetime.date.today().isoformat()
    if started_date != today:
        try:
            if os.path.exists(STATE_PATH):
                os.remove(STATE_PATH)
        except Exception:
            pass
        return "expired", None, None

    expiry_hours = config.get("review_expiry_hours", 1)
    try:
        started_at = datetime.datetime.fromisoformat(state["started_at"])
        elapsed = (datetime.datetime.now() - started_at).total_seconds() / 3600
        if elapsed > expiry_hours:
            try:
                if os.path.exists(STATE_PATH):
                    os.remove(STATE_PATH)
            except Exception:
                pass
            return "expired", None, None
    except Exception:
        pass

    return "resume", state, config


# ── Notifications & narration ─────────────────────────────────────────────────

# Cache the best available espeak voice so we don't probe the filesystem every call
_espeak_voice_cache = None

# Universal narration control — updated by every narrate() call
_active_narration_proc    = None   # currently playing subprocess (paplay or espeak)
_last_narration_text      = None   # in-process fallback for replay
_narration_lock           = threading.Lock()
_narration_stop_requested = False  # set by stop_narration() to suppress piper→espeak fallback
_NARRATION_PID_FILE       = "/tmp/review_narration.pid"   # cross-process kill target
_NARRATION_TEXT_FILE      = "/tmp/review_narration_last.txt"  # cross-process replay text


def is_narrating():
    """Return True if a narration subprocess is currently active."""
    with _narration_lock:
        return (_active_narration_proc is not None
                and _active_narration_proc.poll() is None)


def _write_narration_pid(proc):
    """Write subprocess PID to the cross-process narration kill file."""
    try:
        with open(_NARRATION_PID_FILE, "w") as f:
            f.write(str(proc.pid))
    except Exception:
        pass


def stop_narration():
    """Kill the currently playing narration, if any (works cross-process via PID file)."""
    global _active_narration_proc, _narration_stop_requested
    _narration_stop_requested = True
    stopped = False
    with _narration_lock:
        proc = _active_narration_proc
        if proc is not None:
            try:
                proc.kill()
                stopped = True
            except Exception:
                pass
            _active_narration_proc = None
    # Cross-process kill: dashboard can stop tray's narration via the PID file
    try:
        with open(_NARRATION_PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 9)
        _rlog(f"narrate: cross-process stop (pid={pid})")
        stopped = True
    except FileNotFoundError:
        pass  # no cross-process narration active — normal case
    except Exception:
        pass
    finally:
        try:
            os.unlink(_NARRATION_PID_FILE)
        except Exception:
            pass
    if stopped:
        _rlog("narrate: stopped by request")


def replay_narration(config):
    """Re-narrate the last spoken text (works cross-process via text file)."""
    # Prefer the shared file so dashboard can replay text narrated by the tray process.
    text = None
    try:
        with open(_NARRATION_TEXT_FILE, "r", encoding="utf-8") as f:
            text = f.read().strip() or None
    except FileNotFoundError:
        pass
    except Exception:
        pass
    if text is None:
        text = _last_narration_text  # in-process fallback
    if text:
        _rlog(f"narrate: replaying ({len(text)} chars)")
        narrate(text, config, blocking=False)
    else:
        _rlog("narrate: replay requested but nothing to replay")


def _best_espeak_voice():
    """Return the best available espeak-ng voice. Prefers mbrola (more natural)."""
    global _espeak_voice_cache
    if _espeak_voice_cache is not None:
        return _espeak_voice_cache
    # mbrola US/UK voices — check whether the data file actually exists
    for data_file, voice_id in [
        ("/usr/share/mbrola/us2/us2", "mb-us2"),  # American male  (clear, neutral)
        ("/usr/share/mbrola/us1/us1", "mb-us1"),  # American female
        ("/usr/share/mbrola/us3/us3", "mb-us3"),  # American male
        ("/usr/share/mbrola/en1/en1", "mb-en1"),  # British male
    ]:
        if os.path.exists(data_file):
            _rlog(f"narrate: mbrola voice available — using {voice_id}")
            _espeak_voice_cache = voice_id
            return voice_id
    _espeak_voice_cache = "en-us"
    return "en-us"


def _narrate_espeak(text, blocking):
    """Speak via espeak-ng with tuned settings.

    Uses Hindi voice for Devanagari text, mbrola/en-us otherwise.
    """
    is_hindi = any('\u0900' <= ch <= '\u097F' for ch in text)
    if is_hindi:
        cmd = ["espeak-ng", "-v", "hi", "-s", "130", "-a", "90", text]
    else:
        voice = _best_espeak_voice()
        if voice.startswith("mb-"):
            cmd = ["espeak-ng", "-v", voice, "-s", "145", "-a", "90", text]
        else:
            cmd = ["espeak-ng", "-v", voice, "-s", "135", "-p", "38", "-g", "3", "-a", "90", text]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with _narration_lock:
        global _active_narration_proc
        _active_narration_proc = proc
    _write_narration_pid(proc)
    if blocking:
        proc.wait()


def _narrate_piper(text, config, blocking):
    """Speak via piper neural TTS (much more natural; requires piper + a model file).

    Falls back to espeak if piper is not installed or the model file is missing.
    """
    import shutil, tempfile, sys, threading as _t
    # Resolve piper executable: check current venv bin first, then PATH, then common pip install location
    piper_exe = None
    
    # 1. Check current venv bin if running from one (highest priority)
    venv_bin = os.path.join(os.path.dirname(sys.executable), "piper")
    if os.path.isfile(venv_bin):
        piper_exe = venv_bin
        
    # 2. Check PATH
    if not piper_exe:
        piper_exe = shutil.which("piper")
        
    # 3. Check ~/.local/bin
    if not piper_exe:
        local_bin = os.path.expanduser("~/.local/bin/piper")
        if os.path.isfile(local_bin):
            piper_exe = local_bin

    if not piper_exe or not os.path.isfile(piper_exe):
        _rlog("narrate/piper: piper executable not found — falling back to espeak")
        _narrate_espeak(text, blocking)
        return
    # Pick Hindi model if text contains Devanagari characters, else English model
    is_hindi = any('\u0900' <= ch <= '\u097F' for ch in text)
    if is_hindi:
        model = os.path.expanduser(config.get("piper_model_hi", "") or config.get("piper_model", ""))
    else:
        model = os.path.expanduser(config.get("piper_model", ""))
    if model and not os.path.isabs(model):
        model = os.path.join(_SCRIPT_DIR, model)
    if not model or not os.path.exists(model):
        _rlog("narrate/piper: model not found — falling back to espeak")
        _narrate_espeak(text, blocking)
        return
    try:
        tmp_path = tempfile.mktemp(suffix=".wav")
        # Use Popen+wait so the synthesis process is tracked and stoppable
        synth = subprocess.Popen(
            [piper_exe, "--model", model, "--output_file", tmp_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with _narration_lock:
            global _active_narration_proc
            _active_narration_proc = synth
        # Don't write synth PID — synthesis blocks briefly and can't be usefully killed mid-input
        synth.communicate(input=text.encode(), timeout=15)
        if synth.returncode != 0 or not os.path.exists(tmp_path):
            if _narration_stop_requested:
                _rlog("narrate/piper: synthesis killed by stop request — not falling back")
                return
            _rlog("narrate/piper: piper failed — falling back to espeak")
            _narrate_espeak(text, blocking)
            return
        play = subprocess.Popen(["paplay", tmp_path],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with _narration_lock:
            _active_narration_proc = play
        _write_narration_pid(play)
        if blocking:
            play.wait()
        # Clean up the temp wav after playback (in background if non-blocking)
        def _cleanup():
            play.wait()
            try: os.unlink(tmp_path)
            except Exception: pass
        _t.Thread(target=_cleanup, daemon=True).start()
    except FileNotFoundError:
        _rlog("narrate/piper: piper not installed — falling back to espeak")
        _narrate_espeak(text, blocking)
    except Exception as e:
        _rlog(f"narrate/piper: error ({e}) — falling back to espeak")
        _narrate_espeak(text, blocking)


_UI_NARRATION_DEFAULTS = {
    "step_skipped":    "Step skipped.",
    "review_cancelled": "Review cancelled.",
    "review_complete":  "Evening review complete.",
    "saved_speak_more": "Saved. Speak more, or click Next Step.",
}


def _ui_narration(key, config):
    """Return the configured UI narration string for key, falling back to English default."""
    return config.get("ui_narrations", {}).get(key, _UI_NARRATION_DEFAULTS[key])


def narrate(text, config, blocking=False):
    """Speak text using the configured TTS engine.

    Engine priority (set via review_config.json "tts_engine"):
      "piper"  — neural TTS, natural-sounding; needs piper installed + "piper_model" path
      "espeak" — espeak-ng (default); uses mbrola if installed, otherwise tuned espeak

    blocking=True  — wait for speech to finish before returning.
                     Always pass True before opening the microphone so the TTS
                     audio is not captured as user speech.
    blocking=False — fire-and-forget (default).
    """
    global _last_narration_text, _narration_stop_requested
    if not config.get("voice_narration", True):
        return
    stop_narration()  # stop any currently playing narration before starting new one
    _narration_stop_requested = False  # reset flag so new narration plays normally
    _last_narration_text = text
    # Persist text for cross-process replay, but skip short transient messages
    # ("Processing.", "Recording too quiet") that are never worth replaying.
    if len(text) >= 60:
        try:
            with open(_NARRATION_TEXT_FILE, "w", encoding="utf-8") as _f:
                _f.write(text)
        except Exception:
            pass
    engine = config.get("tts_engine", "espeak")
    try:
        if engine == "piper":
            _narrate_piper(text, config, blocking)
        else:
            _narrate_espeak(text, blocking)
    except FileNotFoundError:
        pass  # espeak-ng not installed — silently skip
    except Exception as e:
        _rlog(f"narrate: error: {e}")


def send_telegram(text, config):
    """Send a Telegram message in the background. Delegates to telegram_service for all logic."""
    def _send():
        try:
            import telegram_service
            telegram_service.send(text, config)
        except ImportError:
            _rlog("telegram: telegram_service module not found — skipping")
    threading.Thread(target=_send, daemon=True).start()


def send_notification(title, message, icon="dialog-information"):
    _rlog(f"NOTIFY: '{title}' — '{message}'")
    try:
        subprocess.run(
            ["notify-send", "-i", icon, "-t", "5000", title, message],
            timeout=5,
            check=False
        )
    except FileNotFoundError:
        print(f"[notify] {title}: {message}")
    except Exception as e:
        print(f"[notify] {title}: {message} (error: {e})")


def send_awaiting_notification(state, config):
    step = get_current_step(state, config)
    if step is None:
        return
    total = get_step_count(config)
    idx = state.get("current_step_index", 0)
    step_name = step.get("section_name", f"Step {idx + 1}")
    count = len(state.get("accumulated_raw", []))
    send_notification(
        f"Evening Review — Step {idx + 1}/{total} Recorded",
        f"'{step_name}' recorded ({count} clip{'s' if count != 1 else ''}). "
        f"Speak more with Ctrl+Alt+V, or click 'Next Step' in the dashboard."
    )
    narrate(_ui_narration("saved_speak_more", config), config)


def send_step_notification(state, config, blocking_narration=False):
    """Send desktop notification and narrate the current step prompt.

    blocking_narration=True  — waits for narration to finish before returning.
                               Pass True when called immediately before recording
                               starts so the mic does not pick up the spoken prompt.
    blocking_narration=False — non-blocking narration (default).
    """
    step = get_current_step(state, config)
    if step is None:
        return
    total = get_step_count(config)
    idx = state.get("current_step_index", 0)
    step_name = step.get("section_name", f"Step {idx + 1}")
    title = f"Evening Review — Step {idx + 1}/{total}"
    message = step.get("prompt_notification", f"Step {idx + 1}: Speak your response.")
    send_notification(title, message)

    # Narrate pending carry-forward tasks before the step prompt (blocking so mic
    # doesn't open while the list is still being spoken)
    if (config.get("carryforward_tasks", False)
            and step.get("step_id") == config.get("carryforward_step_id", 3)):
        tasks = state.get("carryforward_tasks", [])
        if tasks:
            # tasks are dicts {"text": str, ...} or plain strings (legacy)
            task_texts = [t["text"] if isinstance(t, dict) else t for t in tasks[:5]]
            task_list = "، ".join(task_texts)   # max 5 for narration, Hindi list separator
            intro = f"कल के ये काम अभी बाकी हैं: {task_list}"
            narrate(intro, config, blocking=True)

    variants = step.get("narration_variants", [])
    narration_text = (
        __import__("random").choice(variants) if variants
        else f"Step {idx + 1}: {step_name}. Please speak now."
    )
    narrate(narration_text, config, blocking=blocking_narration)
