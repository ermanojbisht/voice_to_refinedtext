# Implementation Steps

> Granular steps per phase. Check off as done.
> See `progress.md` for summary view.

---

## Phase 1 — Fix Active Bugs

### Step 1.1 — Consolidate `_structure_and_advance`

- [x] Read both implementations carefully (`tray_app.py` ~L454, `review_dashboard.py` ~L805)
- [x] Write `review_engine.structure_and_advance(script_dir, engine_instance, state, config)` → `(success: bool, error: str|None)`
  - Takes config snapshot internally (copy of config dict) to be race-safe
  - Handles lock acquire/release
  - Calls transcribe, LLM structure, write_step_to_note, advance_step
  - Returns error string on failure (caller decides how to show it)
- [x] Replace `tray_app.py` implementation with a call to `review_engine.structure_and_advance()`
- [x] Replace `review_dashboard.py` implementation with a call to `review_engine.structure_and_advance()`
- [x] Test: trigger Next Step from both tray menu and dashboard button — same behavior

### Step 1.2 — Single `is_processing` Source of Truth

- [x] Remove `self.is_processing` from `tray_app.py` — delete all reads/writes
- [x] Remove `self.is_processing` from `review_dashboard.py` — delete all reads/writes
- [x] In `tray_app.py`: set `state["processing"] = True` before work starts, `False` after
- [x] In `review_dashboard.py`: read `state.get("processing", False)` from polled state — already done, just trust it now
- [x] Confirm `_poll_state()` in dashboard correctly reads and disables Next button when `processing=True`
- [x] Test: rapid-click Next Step — second click should be blocked by state

### Step 1.3 — File Lock on State Writes

- [x] Add `import fcntl` to `review_engine.py`
- [x] In `_save_state(state)`: wrap file write with `fcntl.flock(f, fcntl.LOCK_EX)` / `LOCK_UN`
- [x] In `_load_state()`: wrap file read with `fcntl.flock(f, fcntl.LOCK_SH)` / `LOCK_UN`
- [x] Remove the 3-retry JSONDecodeError loop from `_load_state()` — replace with single read inside lock
- [x] Test: run tray + dashboard simultaneously, trigger multiple state writes — no corruption

### Step 1.4 — Narration Replay Across Processes

- [x] Add constant `_NARRATION_TEXT_FILE = "/tmp/review_narration_last.txt"` to `review_engine.py`
- [x] In `narrate(text, ...)`: write `text` to `_NARRATION_TEXT_FILE` before spawning TTS process
- [x] In `replay_narration()`: read text from `_NARRATION_TEXT_FILE` instead of `_last_narration_text` variable
- [x] Keep `_last_narration_text` as in-process fallback if file is missing
- [x] Test: narrate from tray, then click replay in dashboard — should replay correctly

---

## Phase 2 — Remove Code Smells

### Step 2.1 — Shared Theme Constants

- [x] Create `theme.py` in project root with all color constants (copy from `review_dashboard.py`)
- [x] Replace color definitions in `tray_app.py` with `from theme import *`
- [x] Replace color definitions in `review_dashboard.py` with `from theme import *`
- [x] Replace color definitions in `config_gui.py` with `from theme import *`
- [x] Replace color definitions in `calibrate_threshold.py` with `from theme import *`
- [x] Run each GUI to confirm colors unchanged

### Step 2.2 — Shared Logger Setup

- [x] Add `get_logger(name, log_file)` to `utils.py`
  - Uses Python standard `logging` module
  - Rotating file handler, consistent format: `[HH:MM:SS] [NAME] message`
  - Returns named logger
- [x] Replace `_tlog()` in `tray_app.py` with `logger = utils.get_logger("tray", log_path)`
- [x] Replace `_rlog()` in `review_engine.py` with `logger = utils.get_logger("engine", log_path)`
- [x] Replace `_rlog()` usage in `review_dashboard.py` with `logger = utils.get_logger("dashboard", log_path)`
- [x] Remove `_LOG_FILE` global from `review_engine.py`
- [x] Test: check `review_debug.log` still has entries from all three components

### Step 2.3 — Delete Dead Code

- [x] Delete `engine.py:run_pipeline()` method (~L197–219)
- [x] Search codebase for any calls to `run_pipeline` — should be zero
- [x] Confirm `engine.py` tests (if any) still pass

### Step 2.4 — Dynamic Review Steps in Config GUI

- [x] In `config_gui.py`, find the hardcoded 6-step loop (~L338–353)
- [x] Replace with: load steps from `self.review_raw["steps"]`, iterate in loop
- [x] Each step row: `step["name"]` as label, `skippable` checkbox, `refine` checkbox (where applicable)
- [x] Test: add a dummy step 7 to `review_config.json` — confirm it appears in GUI automatically

---

## Phase 3 — GUI Configurability

### Step 3.1 — Feature Flags in `config.json`

- [x] Add `FEATURES` block to `config.json`:
  ```json
  "FEATURES": {
    "start_end_sounds": true,
    "clipboard_output": true,
    "markdown_output": false,
    "direct_typing": false,
    "evening_review": true
  }
  ```
- [x] In `engine.py`: read `config["FEATURES"]["start_end_sounds"]` before playing start/end sounds
- [x] In `tray_app.py`: read `config["FEATURES"]["evening_review"]` before showing review menu items
- [x] Update default config loading to include FEATURES block with sensible defaults

### Step 3.2 — Feature Toggles Tab in Config GUI

- [x] Add "Features" tab to `config_gui.py`
- [x] For each FEATURES key: show label + on/off CTkSwitch
- [x] On save: write FEATURES block to `config.json`
- [x] Test: toggle `start_end_sounds` off — confirm no sounds on next recording

### Step 3.3 — Redo Fully Reversible

- [x] In `write_step_to_note()`: before writing, record byte position (`file.tell()`) as `state["last_write_offset"]`; save state
- [x] In `redo_step()`: read `state["last_write_offset"]`; open vault file and truncate at that offset; then call existing redo logic
- [x] Handle edge case: `last_write_offset` missing (step was never written) — skip truncate
- [x] Test: write a step, click Redo — confirm written content disappears from note file

---

## Phase 4 — Documentation

### Step 4.1 — Update README.md

- [x] Verify current file list matches `README.md` File Reference section
- [x] Add `calibrate_threshold.py` entry
- [x] Add `theme.py` entry (after Phase 2.1)
- [x] Update "How It Works" to separate Voice Refiner flow from Evening Review flow
- [x] Remove outdated/wrong feature descriptions (check against actual code)
- [x] Add "Evening Review" as its own section with step list

### Step 4.2 — Update plan.md

- [x] Add learnings from each phase as implemented
- [x] Mark phases complete when all steps done

---

## Phase 5 — Post-Review Correctness Fixes

### Step 5.1 — Remove `self.is_processing` Dual Flag from `tray_app.py`

- [x] Delete `self.is_processing = False` from `__init__` (~L42)
- [x] In `next_step_review`: replace `if self.is_processing:` guard with read from freshly-loaded state (`state.get("processing", False)`)
- [x] Remove `self.is_processing = True` / `self.is_processing = False` from `next_step_review` and `_structure_and_advance` finally block
- [x] Confirm `_review_finished` still works (it sets `self.is_processing = False` — remove that line too)
- [x] Test: rapid-click Next Step from tray — second click blocked by `state["processing"]`

### Step 5.2 — Wire Feature Flags in `_run_normal_mode`

- [x] In `tray_app._run_normal_mode`: wrap `xclip`/`xsel` block with `if self.engine.config.get("FEATURES", {}).get("clipboard_output", True):`
- [x] Replace `self.engine.config.get("DIRECT_TYPING")` with `self.engine.config.get("FEATURES", {}).get("direct_typing", False)`
- [x] Test: toggle `clipboard_output` off in config GUI — confirm text not copied on next recording
- [x] Test: toggle `direct_typing` off — confirm no keyboard typing

### Step 5.3 — Public `accumulate_clip()` in `review_engine`

- [x] Add `accumulate_clip(state, raw_text) -> dict` to `review_engine.py`:
  - Appends `raw_text` to `state["accumulated_raw"]`
  - Sets `state["awaiting_more"] = True`
  - Calls `_save_state(state)`
  - Returns updated state
- [x] In `tray_app._handle_review_step`: replace manual state mutation + `review_engine._save_state(...)` call with `self.review_state = review_engine.accumulate_clip(self.review_state, raw_text)`
- [x] Confirm `review_engine._save_state` is no longer called from `tray_app.py`

---

## Phase 6 — Clean Public API for `review_engine`

### Step 6.1 — Rename `_load_state` → `load_state` in `review_engine.py`

- [ ] In `review_engine.py`: `replace_all=True` on `_load_state` → `load_state` (renames definition + all ~6 internal calls)
- [ ] Confirm `_save_state` is NOT renamed (stays private)

### Step 6.2 — Rename 8 read-only helpers to public names

- [ ] `_fmt_duration` → `fmt_duration` (no internal callers — rename definition only)
- [ ] `_get_focus_word_counts` → `get_focus_word_counts` (`replace_all` — also updates `_get_weekly_focus_trend`)
- [ ] `_get_daily_note_path` → `get_daily_note_path` (`replace_all` — many internal callers)
- [ ] `_extract_evening_review_section` → `extract_evening_review_section` (`replace_all` — updates `_read_last_n_notes`)
- [ ] `_extract_step_section` → `extract_step_section` (no internal callers — rename definition only)
- [ ] `_read_last_n_isolated_notes` → `get_isolated_notes` (no internal callers — rename definition only)
- [ ] `_mark_task_done` → `mark_task_done` (no internal callers — rename definition only)
- [ ] `_load_streak` → `load_streak` (`replace_all` — updates `update_streak` and `initialize_review`)
- [ ] Grep `_get_weekly_focus_trend` and confirm it calls `get_focus_word_counts` after rename

### Step 6.3 — Add `regenerate_brief(script_dir, config)` to `review_engine.py`

- [ ] Add public function after `_run_context_brief`:
  - Load state; return immediately if None
  - `_bust_brief_cache(script_dir, date_str)`
  - Clear `context_brief`, `context_brief_en`, `context_brief_hi` from state; set `context_ready=False`
  - `_save_state(state)`
  - Spawn `_run_context_brief` in daemon thread
- [ ] Confirm `_bust_brief_cache`, `_save_state`, `_run_context_brief` remain private

### Step 6.4 — Remove `self.is_processing` from `review_dashboard.py`

- [ ] Delete `self.is_processing = False` from `__init__` (L81)
- [ ] In `_update_ui`: change `busy = self.is_processing or remote_processing` → `busy = remote_processing`
- [ ] In `_update_context_panel`: change `busy = self.is_processing or state.get(...)` → `busy = state.get("processing", False)`
- [ ] In `_do_next`: remove `if self.is_processing: return` guard; remove `self.is_processing = True` and `self._update_ui(state)` call; rely on state check
- [ ] In `_structure_and_advance` finally: remove `self.is_processing = False`
- [ ] Grep dashboard for remaining `is_processing` — must be zero

### Step 6.5 — Update all external callers to public API

**review_dashboard.py:**
- [ ] All `review_engine._load_state()` → `review_engine.load_state()`
- [ ] `review_engine._fmt_duration(...)` → `review_engine.fmt_duration(...)`  (2 places)
- [ ] `review_engine._read_last_n_isolated_notes(...)` → `review_engine.get_isolated_notes(...)`
- [ ] `review_engine._extract_step_section(...)` → `review_engine.extract_step_section(...)`
- [ ] `review_engine._mark_task_done(...)` → `review_engine.mark_task_done(...)`
- [ ] `review_engine._get_focus_word_counts(...)` → `review_engine.get_focus_word_counts(...)`
- [ ] `_regen_brief`: replace body with 3 lines calling `review_engine.regenerate_brief(script_dir, self.config)`

**tray_app.py:**
- [ ] 4× `review_engine._load_state()` → `review_engine.load_state()`

**morning_brief.py:**
- [ ] `review_engine._get_daily_note_path(...)` → `review_engine.get_daily_note_path(...)`
- [ ] `review_engine._extract_evening_review_section(...)` → `review_engine.extract_evening_review_section(...)`
- [ ] `review_engine._extract_step_section(...)` → `review_engine.extract_step_section(...)`

**evening_reminder.py:**
- [ ] `review_engine._load_streak(...)` → `review_engine.load_streak(...)`

### Step 6.6 — Final verification

- [ ] `grep -r "review_engine\._[a-z]" *.py` — only `_rlog` shim should remain
- [x] `grep "self\.is_processing" review_dashboard.py` — zero results

---

## Phase 7 — Atomic Processing Lock (TOCTOU Fix)

### Step 7.1 — Add `_PROCESSING_LOCK_PATH` and lock helpers to `review_engine.py`

- [ ] Add constant near `STATE_PATH`: `_PROCESSING_LOCK_PATH = "/tmp/review_processing.lock"`
- [ ] Add `_acquire_processing_lock() -> fd | None`:
  - `fd = open(_PROCESSING_LOCK_PATH, "w")`
  - `fcntl.flock(fd, LOCK_EX | LOCK_NB)`
  - Return `fd` on success
  - On `BlockingIOError` or `OSError`: close fd, return `None`
- [ ] Add `_release_processing_lock(fd)`:
  - `fcntl.flock(fd, LOCK_UN)`
  - `fd.close()`
  - Both wrapped in try/except

### Step 7.2 — Rewrite `structure_and_advance` to use the file lock

- [ ] At function entry: call `_acquire_processing_lock()`
  - If returns `None`: log "lock held by another process" → `return False, None, True`
- [ ] Remove the old soft check: `if fresh_state.get("processing"): return False, None, True`
  - Reason: the file lock is now the definitive guard; the old check was the TOCTOU
- [ ] Keep `fresh_state["processing"] = True; _save_state(fresh_state)` — this is now a display signal only, not a guard
- [ ] Rename `acquired_lock` variable to `_processing_set` to reflect its new meaning (UI signal, not the real lock)
- [ ] In `finally`: clear `processing` from state as before; then call `_release_processing_lock(lock_fd)`
- [ ] Verify `skip_step` (called internally at line ~1209) does NOT attempt to acquire the lock — it must not

### Step 7.3 — Final verification

- [ ] Read the final `structure_and_advance` function and confirm: acquire lock → load state → set processing display → work → finally: clear processing → release lock
- [ ] Grep for `_PROCESSING_LOCK_PATH` — appears only in `review_engine.py`
- [ ] Grep for `acquired_lock` — must be zero (renamed away)
- [ ] Update plan.md notes and progress.md

---

## Phase 8 — Tray Completion Sync

### Step 8.1 — Add `_watch_review_completion()` to `tray_app.py`

- [ ] Add method after `_review_finished()`:
  - Loop while `self.is_in_review and self.running`
  - Sleep 2 seconds per iteration (use `time.sleep(2)`)
  - After sleep, check `self.is_in_review` again (may have been cleared by another path)
  - Call `review_engine.is_review_active(self.script_dir)` — if not active, call `self._review_finished()` and break
  - Mark as daemon thread so it does not block process exit

### Step 8.2 — Start watcher from `start_review()`

- [ ] After `self.is_in_review = True` in `start_review()`, add:
  `threading.Thread(target=self._watch_review_completion, daemon=True).start()`

### Step 8.3 — Verify no double-call to `_review_finished()`

- [ ] Confirm `_review_finished()` is idempotent: calling it when already `is_in_review=False` does no harm
  - It sets `is_in_review = False` (already False → no-op)
  - It sets `review_state = None` (already None → no-op)
  - It calls `_refresh_menu()` (harmless)
- [ ] Confirm the watcher thread exits after calling `_review_finished()` (the `break` ensures this)
- [ ] Confirm the watcher thread exits naturally when `_review_finished()` is called by another path
  (next iteration sees `self.is_in_review=False` → loop condition fails → exits)

### Step 8.4 — Update docs

- [ ] Add Known Issues entry to README.md
- [ ] Mark Phase 8 complete in progress.md and plan.md notes

---

## Phase 9 — Edge-Case Hardening

### Step 9.1 — Guard `start_review()` against re-entry

- [ ] In `tray_app.py:start_review()`: add at entry `if self.is_in_review: _tlog("start_review: already in review, ignoring"); return`

### Step 9.2 — Guard `_do_skip()` and `_do_redo()` in dashboard

- [ ] In `review_dashboard.py:_do_skip()`: after loading state and None-check, add `if not state.get("active", True): return`
- [ ] In `review_dashboard.py:_do_redo()`: same guard

### Step 9.3 — Guard `_handle_review_step()` against `review_config=None`

- [ ] In `tray_app.py:_handle_review_step()`: at function entry add `if self.review_config is None: _tlog("_handle_review_step: review_config gone (cancel race), ignoring"); return`

### Step 9.4 — Verification

- [ ] Grep `_do_skip` and `_do_redo` in dashboard — both have active guard
- [ ] Grep `start_review` — re-entry guard present at top
- [ ] Grep `_handle_review_step` — review_config guard present at top
- [ ] Update progress.md and plan.md

---

## Phase 10 — Final Hardening

### Step 10.1 — Defensive guard in `initialize_review()`

- [ ] At top of `initialize_review()` in `review_engine.py` (before any writes): check `if os.path.exists(STATE_PATH)` and if so call `is_review_active()` — if active, log and return immediately
- [ ] Confirm the guard does not fire when called from `start_review()` (which already cleared `is_in_review` check) — it should only trigger if called while state file exists and active

### Step 10.2 — `active` guard in `_do_next()`

- [ ] In `review_dashboard.py:_do_next()`, after `if state is None: return`, add `if not state.get("active", True): return`
- [ ] Confirm all three dashboard action buttons now share the same guard pattern

### Step 10.3 — Discard orphaned review audio

- [ ] In `tray_app.py:_handle_review_step()`, where `fresh_state is None`: replace `_run_normal_mode(raw_text)` with `self._notify("Evening Review", "Review session ended — recording discarded.")` + `return`
- [ ] Confirm: no LLM call, no clipboard write, no typing for orphaned review audio

### Step 10.4 — Verification + docs

- [ ] `grep "_run_normal_mode" tray_app.py` — confirm not called from `_handle_review_step`
- [ ] `grep "active" review_dashboard.py` — all three `_do_*` buttons have the guard
- [ ] Update README Known Issues; update progress.md and plan.md

---

## Phase 11 — Pending Task Story Engine

### Step 11.1 — Add config defaults

- [x] In `review_engine.py` default config dict: add `"pending_task_lookback_days": 7`, `"pending_task_warn_threshold": 3`, `"pending_task_critical_threshold": 5`
- [x] In `review_config.json`: add same three keys with same defaults
- [x] Confirm `load_review_config()` returns these keys with correct defaults when missing from file

### Step 11.2 — Add `_parse_priority_tasks(text)` in `review_engine.py`

- [x] Accept a string (content of `### Tomorrow's Priorities` section)
- [x] Parse each line: `- [x] ...` → `{"text": "...", "done": False}`; `- [x] ...` → `{"text": "...", "done": True}`
- [x] Skip blank lines and non-task lines silently
- [x] Return list of task dicts (preserving order)
- [x] Unit-check: feed sample text, confirm correct done/undone split

### Step 11.3 — Add `_normalize_task(text)` in `review_engine.py`

- [x] Lowercase, `re.sub(r'[^\w\s]', '', text)` to strip punctuation, `re.sub(r'\s+', ' ', text)` to compress spaces, `.strip()`
- [x] Add `_tasks_match(a, b)` helper: returns True if normalized forms are equal, OR if word-overlap ratio ≥ 0.60 (lowered: singular/plural token diff) (using `len(words_a & words_b) / max(len(words_a), len(words_b))`)
- [x] Confirm: "Resolve field officer errors" matches "Resolve errors with field officers" (word overlap)
- [x] Confirm: "Enter cost of DPR" does NOT match "Enter budget estimate" (below threshold)

### Step 11.4 — Add `get_pending_tasks(script_dir, config)` in `review_engine.py`

- [x] Read `lookback_days = config.get("pending_task_lookback_days", 7)`; return `[]` immediately if `lookback_days == 0`
- [x] Build `days_data`: for each of last `lookback_days` days (today−1 back to today−lookback_days):
  - Call `get_daily_note_path(script_dir, config, date_str)`
  - If note missing: skip that day (do not error)
  - Extract `### Tomorrow's Priorities` via `extract_step_section`
  - Parse with `_parse_priority_tasks` → store `{"date": date_str, "tasks": [...]}`
- [x] Build `done_set`: normalized text of every `done=True` task across ALL days
- [x] For each task in `days_data[0]` (yesterday) that is `done=False` and not in `done_set`:
  - Walk through `days_data[1:]` to find earliest day where the same task appeared (using `_tasks_match`)
  - `days_pending = (date_yesterday − first_seen_date).days + 1`
  - Append `{"text": task["text"], "days_pending": days_pending, "first_seen": first_seen_str}`
- [x] Sort result by `days_pending` descending (oldest first)
- [x] Return the sorted list; return `[]` if yesterday's note missing

### Step 11.5 — Add `build_pending_story(pending_tasks, config)` in `review_engine.py`

- [x] Read `lang = config.get("context_brief_language", "en")`, `warn = config.get("pending_task_warn_threshold", 3)`, `crit = config.get("pending_task_critical_threshold", 5)`
- [x] For each task, assign label:
  - `days >= crit` → `🚨 {days} days pending`
  - `days >= warn` → `⚠️ {days} days pending`
  - `days == 2` → `📌 Since 2 days`
  - `days == 1` → `🆕 New today`
- [x] Build body: one line per task `"{label} — {text}"`
- [x] Append closing summary line (EN: `"Your oldest pending task is {max} days old — consider acting on it today."`; HI: `"आपका सबसे पुराना लंबित कार्य {max} दिनों से है — इसे आज निपटाने पर विचार करें।"`)
- [x] If `lang == "hi"`: translate bucket labels too (`🚨 {N} दिनों से लंबित`, `⚠️ {N} दिनों से`, `📌 2 दिनों से`, `🆕 आज नया`)
- [x] Return the full story string

### Step 11.6 — Update `morning_brief.py`

- [x] After `_get_priorities()` call (existing), call `pending = review_engine.get_pending_tasks(script_dir, config)`
- [x] If `pending`: call `story = review_engine.build_pending_story(pending, config)`
- [x] Set `full_narration = story + "\n\n" + intro` (pending story narrated first; today's tasks second)
- [x] In `send_notification`: include pending count in subtitle (e.g. `f"{len(pending)} tasks pending · {priorities[:200]}"`)
- [x] In `send_telegram`: prepend pending story before today's priorities
- [x] If `not pending` and `not priorities`: existing "no priorities found" path unchanged
- [x] If `not pending` but priorities exist: existing single-priorities path unchanged

### Step 11.7 — Expose in config GUI

- [x] In `config_gui.py` Notifications tab: add labeled integer entry for `pending_task_lookback_days`
  - Label: `"Pending task lookback days (0 = off)"`; default 7; accepts any positive integer or 0
- [x] On save: write `pending_task_lookback_days` as integer to `review_config.json`
- [x] Confirm value round-trips: set to 14, save, re-open Settings → shows 14

### Step 11.8 — Verification + docs

- [x] Manual test: ensure at least 2 days have the same unchecked task in `### Tomorrow's Priorities`; run `python3 morning_brief.py`; confirm pending story appears in narration + notification
- [x] Test edge case: `pending_task_lookback_days = 0` → no pending story, existing brief unchanged
- [x] Test edge case: all tasks checked → `get_pending_tasks` returns `[]` → no pending story
- [x] Test edge case: some notes missing (gaps in daily review) → function skips missing days gracefully
- [x] Update README.md: new feature bullet + 3 new config table rows
- [x] Update `progress.md`: mark 11.1–11.8 complete
- [x] Update `plan.md` notes: mark Phase 11 complete
