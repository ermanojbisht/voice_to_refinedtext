#!/usr/bin/env python3
import os
import json
import datetime
import subprocess

STATE_PATH = "/tmp/review_state.json"
_LOG_FILE = None  # set by init_logging()

def init_logging(script_dir):
    global _LOG_FILE
    _LOG_FILE = os.path.join(script_dir, "review_debug.log")

def _rlog(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [review_engine] {msg}"
    print(line)
    log_path = _LOG_FILE or "/tmp/review_debug.log"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_review_config(script_dir):
    config_path = os.path.join(script_dir, "review_config.json")
    default_config = {
        "vault_paths": {
            "base_vault": "~/learning_vault",
            "daily_notes": "~/learning_vault/My Daily Notes",
            "wellness_notes": "~/learning_vault/My Daily Notes/Wellness"
        },
        "review_expiry_hours": 1,
        "last_n_days_context": 1,
        "review_steps": [
            {
                "step_id": 1,
                "section_name": "Focus Word",
                "prompt_notification": "Step 1/4: Speak today's core focus word or overarching theme.",
                "markdown_template": "### \U0001f4cc Focus Word\n**{{text}}**\n",
                "isolate_file": False,
                "skippable": True,
                "refine": True
            },
            {
                "step_id": 2,
                "section_name": "Achievements",
                "prompt_notification": "Step 2/4: What did you accomplish, build, or unblock today?",
                "markdown_template": "### \U0001f6e0\ufe0f Key Achievements\n{{text}}\n",
                "isolate_file": False,
                "skippable": True,
                "refine": True
            },
            {
                "step_id": 3,
                "section_name": "Tomorrow's Priorities",
                "prompt_notification": "Step 3/4: What tasks need immediate attention tomorrow?",
                "markdown_template": "### \u23f3 Tomorrow's Priorities\n{{text}}\n",
                "isolate_file": False,
                "skippable": True,
                "refine": True
            },
            {
                "step_id": 4,
                "section_name": "Wellness Log",
                "prompt_notification": "Step 4/4: Any wellness or personal reflections? (Speak or Skip).",
                "markdown_template": "### \U0001f9e0 Wellness Log\n*{{timestamp}}*: {{text}}\n",
                "isolate_file": True,
                "skippable": True,
                "refine": False
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
            default_config.update(user_config)
        except Exception:
            pass
    return default_config


def _save_state(state):
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        _rlog(f"State saved: step={state.get('current_step_index')}, active={state.get('active')}")
    except Exception as e:
        _rlog(f"ERROR saving state: {e}")


def _load_state():
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            _rlog(f"State file not found at {STATE_PATH}")
    except Exception as e:
        _rlog(f"ERROR loading state: {e}")
    return None


def is_review_active(script_dir):
    state = _load_state()
    if state is None:
        _rlog("is_review_active → False (no state file)")
        return False, None
    if not state.get("active", False):
        _rlog("is_review_active → False (active=False in state)")
        return False, None

    today = datetime.date.today().isoformat()
    if state.get("date") != today:
        _rlog(f"is_review_active → False (date mismatch: state={state.get('date')} today={today})")
        return False, None

    config = load_review_config(script_dir)
    expiry_hours = config.get("review_expiry_hours", 1)
    try:
        started_at = datetime.datetime.fromisoformat(state["started_at"])
        elapsed = (datetime.datetime.now() - started_at).total_seconds() / 3600
        if elapsed > expiry_hours:
            _rlog(f"is_review_active → False (expired: elapsed={elapsed:.2f}h > limit={expiry_hours}h)")
            return False, None
    except Exception as e:
        _rlog(f"is_review_active: expiry check error (ignored): {e}")

    _rlog(f"is_review_active → True (step={state.get('current_step_index')})")
    return True, state


def initialize_review(script_dir):
    init_logging(script_dir)
    _rlog("=" * 50)
    _rlog("initialize_review called")
    config = load_review_config(script_dir)

    vault_paths = config.get("vault_paths", {})
    daily_notes_dir = os.path.expanduser(vault_paths.get("daily_notes", "~/learning_vault/My Daily Notes"))
    wellness_dir = os.path.expanduser(vault_paths.get("wellness_notes", "~/learning_vault/My Daily Notes/Wellness"))

    _rlog(f"Daily notes dir: {daily_notes_dir}")
    _rlog(f"Wellness dir: {wellness_dir}")

    try:
        os.makedirs(daily_notes_dir, exist_ok=True)
        os.makedirs(wellness_dir, exist_ok=True)
        _rlog("Vault directories ensured")
    except Exception as e:
        _rlog(f"ERROR creating vault dirs: {e}")

    now = datetime.datetime.now()
    state = {
        "active": True,
        "current_step_index": 0,
        "date": now.date().isoformat(),
        "started_at": now.isoformat(),
        "last_written": None,
        "awaiting_more": False
    }
    _save_state(state)
    _rlog(f"Review initialized. Steps: {len(config.get('review_steps', []))}")
    send_step_notification(state, config)


def get_current_step(state, config):
    steps = config.get("review_steps", [])
    idx = state.get("current_step_index", 0)
    if 0 <= idx < len(steps):
        return steps[idx]
    return None


def get_step_count(config):
    return len(config.get("review_steps", []))


def _get_daily_note_path(script_dir, config, date_str=None):
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    vault_paths = config.get("vault_paths", {})
    daily_notes_dir = os.path.expanduser(vault_paths.get("daily_notes", "~/learning_vault/My Daily Notes"))
    return os.path.join(daily_notes_dir, f"{date_str}.md")


def _get_wellness_note_path(script_dir, config, date_str=None):
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    vault_paths = config.get("vault_paths", {})
    wellness_dir = os.path.expanduser(vault_paths.get("wellness_notes", "~/learning_vault/My Daily Notes/Wellness"))
    return os.path.join(wellness_dir, f"{date_str}.md")


def append_to_note(script_dir, config, step, text, state):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    date_str = now.date().isoformat()

    is_continuation = state.get("awaiting_more", False)
    if is_continuation:
        # Continuation recording: just append the text without repeating the section header
        block = f"{text}\n"
    else:
        template = step.get("markdown_template", "{{text}}\n")
        block = template.replace("{{text}}", text).replace("{{timestamp}}", timestamp).replace("{{date}}", date_str)

    if step.get("isolate_file", False):
        file_path = _get_wellness_note_path(script_dir, config, date_str)
    else:
        file_path = _get_daily_note_path(script_dir, config, date_str)

    _rlog(f"append_to_note: step='{step.get('section_name')}' file='{file_path}'")
    _rlog(f"append_to_note: text_preview='{text[:60]}...' " if len(text) > 60 else f"append_to_note: text='{text}'")

    try:
        parent_dir = os.path.dirname(file_path)
        os.makedirs(parent_dir, exist_ok=True)

        file_exists = os.path.exists(file_path)
        with open(file_path, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write(f"# Daily Note — {date_str}\n\n")
            f.write(block)
        _rlog(f"append_to_note: SUCCESS wrote {len(block)} chars to {file_path}")
    except Exception as e:
        _rlog(f"ERROR in append_to_note: {e}")
        return

    state["last_written"] = {"file": file_path, "block": block}
    _save_state(state)


def advance_step(script_dir, state, config):
    steps = config.get("review_steps", [])
    prev = state.get("current_step_index", 0)
    state["current_step_index"] = prev + 1
    state["last_written"] = None
    state["awaiting_more"] = False
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
    state["current_step_index"] = prev + 1
    state["last_written"] = None
    state["awaiting_more"] = False
    _rlog(f"skip_step: {prev} → {state['current_step_index']} (total={len(steps)})")

    if state["current_step_index"] >= len(steps):
        _rlog("skip_step: last step skipped, calling complete_review")
        complete_review(script_dir, None, state, config)
    else:
        _save_state(state)
        send_step_notification(state, config)


def redo_step(script_dir, state, config):
    last_written = state.get("last_written")
    if last_written:
        file_path = last_written.get("file")
        block = last_written.get("block")
        if file_path and block and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                last_occurrence = content.rfind(block)
                if last_occurrence != -1:
                    content = content[:last_occurrence] + content[last_occurrence + len(block):]
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
            except Exception as e:
                _rlog(f"ERROR in redo_step file edit: {e}")
        state["last_written"] = None
        state["awaiting_more"] = False
        _save_state(state)

    send_step_notification(state, config)


def cancel_review(script_dir):
    _rlog("cancel_review called")
    try:
        if os.path.exists(STATE_PATH):
            os.remove(STATE_PATH)
            _rlog("State file deleted")
    except Exception as e:
        _rlog(f"ERROR deleting state file: {e}")
    send_notification("Evening Review", "Review cancelled. Returning to normal mode.")


def _generate_and_prepend_summary(script_dir, daily_note_path, date_str):
    """Runs in a background thread: generates an AI summary and prepends it to the daily note."""
    _rlog("_generate_and_prepend_summary: starting background summary generation")
    try:
        if not os.path.exists(daily_note_path):
            _rlog("_generate_and_prepend_summary: daily note not found, skipping")
            return
        with open(daily_note_path, "r", encoding="utf-8") as f:
            note_content = f.read()
        if not note_content.strip():
            _rlog("_generate_and_prepend_summary: daily note empty, skipping")
            return

        import utils
        main_config = utils.load_config(script_dir)
        host = main_config.get("OLLAMA_HOST", "http://localhost:11434")
        models = main_config.get("OLLAMA_MODELS", {})
        model = models.get("en", "qwen2.5:3b")
        prompt = f"In 2-3 sentences, summarize this daily review entry:\n\n{note_content}"
        response = utils.call_ollama(host, model, prompt, [], main_config.get("TEMPERATURE", 0.1))
        if "error" in response:
            _rlog(f"_generate_and_prepend_summary: Ollama error: {response['error']}")
            return

        summary = utils.clean_response(response.get("response", "")).strip()
        if not summary:
            _rlog("_generate_and_prepend_summary: empty summary returned")
            return

        summary_block = f"### \U0001f4cb Daily Summary\n{summary}\n\n---\n\n"
        with open(daily_note_path, "r", encoding="utf-8") as f:
            existing = f.read()
        with open(daily_note_path, "w", encoding="utf-8") as f:
            f.write(summary_block + existing)
        _rlog(f"_generate_and_prepend_summary: summary prepended ({len(summary)} chars)")
        send_notification("Evening Review", "AI summary added to daily note.")
    except Exception as e:
        _rlog(f"_generate_and_prepend_summary: ERROR: {e}")


def complete_review(script_dir, engine_instance, state, config):
    import threading
    date_str = state.get("date", datetime.date.today().isoformat())
    daily_note_path = _get_daily_note_path(script_dir, config, date_str)

    _rlog(f"complete_review: date={date_str} daily_note={daily_note_path}")

    # Ensure the daily note file exists — create with header if no steps were recorded
    if not os.path.exists(daily_note_path):
        try:
            parent_dir = os.path.dirname(daily_note_path)
            os.makedirs(parent_dir, exist_ok=True)
            with open(daily_note_path, "w", encoding="utf-8") as f:
                f.write(f"# Daily Note — {date_str}\n\n")
                f.write("*No entries recorded for this review session.*\n")
            _rlog(f"complete_review: created empty daily note at {daily_note_path}")
        except Exception as e:
            _rlog(f"complete_review: ERROR creating daily note: {e}")
    else:
        _rlog(f"complete_review: daily note already exists, will append summary")

    # Delete state file immediately so is_review_active returns False right away
    try:
        if os.path.exists(STATE_PATH):
            os.remove(STATE_PATH)
            _rlog("complete_review: state file deleted")
    except Exception as e:
        _rlog(f"complete_review: ERROR deleting state file: {e}")

    # Notify user immediately — don't wait for summary
    send_notification("Evening Review Complete", "All steps done! Generating summary in background...")

    # Generate AI summary in background so it doesn't block the UI
    t = threading.Thread(
        target=_generate_and_prepend_summary,
        args=(script_dir, daily_note_path, date_str),
        daemon=True
    )
    t.start()
    _rlog("complete_review: background summary thread started")


def check_startup_state(script_dir):
    config = load_review_config(script_dir)
    state = _load_state()

    if state is None:
        return "none", None, None

    today = datetime.date.today().isoformat()
    if state.get("date") != today:
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


def send_notification(title, message, icon="dialog-information"):
    _rlog(f"NOTIFY: '{title}' — '{message}'")
    try:
        subprocess.run(
            ["notify-send", "-i", icon, title, message],
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
    send_notification(
        f"Evening Review — Step {idx + 1}/{total} Saved",
        f"'{step_name}' saved. Speak more with Ctrl+Alt+V, or click 'Next Step' in the tray."
    )


def send_step_notification(state, config):
    step = get_current_step(state, config)
    if step is None:
        return
    total = get_step_count(config)
    idx = state.get("current_step_index", 0)
    title = f"Evening Review — Step {idx + 1}/{total}"
    message = step.get("prompt_notification", f"Step {idx + 1}: Speak your response.")
    send_notification(title, message)
