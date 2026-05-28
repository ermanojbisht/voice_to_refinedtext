# Refactoring Plan: Voice Refiner

> **Status**: Complete ✅ (all 10 phases)  
> **Started**: 2026-05-22  **Completed (Phases 1–4)**: 2026-05-22  
> **Scope**: Fix correctness bugs, reduce duplication, improve configurability. No directory restructure.

---

## What This Plan Is NOT

- Not a full rewrite
- Not moving files into `core/`, `review/`, `shared/` subdirectories
- Not adding new features
- Not changing Obsidian note formats or config schemas

---

## What This Plan IS

Fix four real bugs, clean up three code smells, add GUI configurability for features, update docs.

---

## The Two Applications (Conceptual, Not File-Level)

```
App 1 — Voice Refiner (original goal)
  Record → Whisper → Ollama → Clipboard / Markdown / Typing
  Files: engine.py, tray_app.py (normal mode), voice_to_ai_clipboard.py

App 2 — Evening Review (built on top)
  6-step structured capture → Obsidian vault notes
  Files: review_engine.py, review_dashboard.py, tray_app.py (review mode)
```

App 1 must work independently. App 2 uses App 1's engine but must not break when features are added to either.

---

## Phase 1 — Fix Active Bugs (Priority: Critical)

These are correctness issues that can cause data loss or race conditions right now.

### 1.1 — Consolidate `_structure_and_advance`

**Problem**: Identical logic duplicated in `tray_app.py` (~L454) and `review_dashboard.py` (~L805). Minor differences exist (error notification style, config snapshot). If you fix a bug in one, the other breaks.

**Fix**: Move the canonical implementation into `review_engine.py` as `structure_and_advance(script_dir, engine_instance, state, config)`. Both files call this. Each keeps only its thread-spawning wrapper.

### 1.2 — Single Source of Truth for `is_processing`

**Problem**: Three separate flags:
- `tray_app.self.is_processing` (in-memory)
- `review_dashboard.self.is_processing` (in-memory)
- `state["processing"]` in `/tmp/review_state.json` (disk)

All three can briefly disagree. Dashboard polling (500ms) sees stale tray state.

**Fix**: Remove both in-memory flags. Use `state["processing"]` as the only truth. Dashboard reads it on every poll — this is already happening, just not trusted.

### 1.3 — File Lock on State Writes

**Problem**: Both tray and dashboard write `/tmp/review_state.json` concurrently. No file lock. Corrupted JSON is silently masked by a 3-retry catch in `_load_state()`.

**Fix**: Add `fcntl.flock` in `review_engine._save_state()` (exclusive) and `_load_state()` (shared). Remove the retry hack once locking is in place.

### 1.4 — Narration Replay Across Processes

**Problem**: `_last_narration_text` is a per-process global in `review_engine.py`. If tray narrates the context brief, dashboard's copy of this variable is empty. Dashboard's replay button has nothing to replay.

**Fix**: Write narration text to `/tmp/review_narration_last.txt` when narration starts. `replay_narration()` reads from file instead of in-memory variable. Both processes share one source of truth.

---

## Phase 2 — Remove Code Smells (Priority: High)

Safe refactors with no behavior change.

### 2.1 — Shared Theme Constants

**Problem**: Catppuccin color palette (`BG`, `SURFACE`, `ACCENT`, etc.) copy-pasted in 4 files: `tray_app.py`, `review_dashboard.py`, `config_gui.py`, `calibrate_threshold.py`.

**Fix**: Create `theme.py` with all color constants. All 4 files import from it.

### 2.2 — Shared Logger Setup

**Problem**: Three separate `_tlog`/`_rlog` setups across `tray_app.py`, `review_engine.py`, `review_dashboard.py`. Global `_LOG_FILE` in `review_engine` can race with initialization.

**Fix**: Add `get_logger(name)` function to `utils.py`. All files call `logger = utils.get_logger(__name__)`. One log file, consistent format, no globals.

### 2.3 — Delete Dead Code

**Problem**: `engine.py:run_pipeline()` (~L197) is never called and references `review_engine.append_to_note()` which does not exist.

**Fix**: Delete the method.

### 2.4 — Dynamic Review Steps in Config GUI

**Problem**: `config_gui.py` (L338–353) hardcodes 6 step checkboxes. Adding step 7 requires a code change.

**Fix**: Load step list from `review_config["steps"]` and build checkboxes in a loop. GUI adapts to whatever steps are in config.

---

## Phase 3 — GUI Configurability (Priority: Medium)

Make features independently switchable without editing code.

### 3.1 — Feature Flags in `config.json`

Add a `FEATURES` block:
```json
"FEATURES": {
  "start_end_sounds": true,
  "clipboard_output": true,
  "markdown_output": false,
  "direct_typing": false,
  "evening_review": true
}
```
These already exist as separate config keys. This just groups them clearly and adds `evening_review` toggle.

### 3.2 — Feature Toggles Tab in Config GUI

New tab "Features" in `config_gui.py` with on/off switches for each `FEATURES` entry. When `evening_review = false`, tray hides the review menu item — no restart needed.

### 3.3 — Redo Fully Reversible

**Problem**: `redo_step()` resets the step counter but leaves the already-written note content in the vault file.

**Fix**: `write_step_to_note()` records the byte offset where it started writing into `state["last_write_offset"]`. `redo_step()` truncates the file at that offset before resetting the step. User gets a clean redo.

---

## Phase 4 — Documentation (Priority: Always Last)

### 4.1 — Update README.md
- Reflect current file list (add `calibrate_threshold.py`, remove outdated references)
- Update feature list to match reality
- Add section: "Evening Review" as distinct from "Voice Refiner"
- Update "How It Works" flow diagram

### 4.2 — Update This Plan
- Edit this file as implementation progresses
- Add learnings in the "Notes" section below

---

## Phase 7 — Atomic Processing Lock (TOCTOU Fix) (Priority: High)

### Root Cause

`structure_and_advance()` does a check-then-set on `state["processing"]` that is not atomic between processes:

```
Process A: load state → see processing=False → (gap) → set processing=True → work
Process B: load state → see processing=False → (gap) → set processing=True → work ← duplicate
```

`fcntl.flock` on the state file serialises the individual writes but NOT the check-then-set sequence. Two processes can both pass the check before either sets the flag.

### Why only `structure_and_advance` gets the lock

`structure_and_advance` calls `skip_step` internally (when no raw text is accumulated). `fcntl.flock` on Linux is per-open-file-description. If the same process opens the lock file a second time and tries `LOCK_EX|LOCK_NB`, the OS denies it — the process deadlocks itself. So `skip_step` and `redo_step` must NOT acquire the processing lock.

Protection for skip/redo comes from the existing `state.get("processing")` checks in their callers: if `structure_and_advance` holds the lock and has set `processing=True`, dashboard's `_do_skip`/`_do_redo` and tray's `skip_review_step`/`redo_review_step` will bail before calling them.

**Residual risk** (documented, accepted): two simultaneous skip or redo calls with no LLM processing active. Requires near-simultaneous user action across two UIs when `processing=False`. Consequence is minor (double-skip advances step twice; double-redo is idempotent). Not worth the deadlock complexity of locking skip/redo.

### 7.1 — Add `_PROCESSING_LOCK_PATH` + lock helpers

Add to `review_engine.py` near the other path constants:
```python
_PROCESSING_LOCK_PATH = "/tmp/review_processing.lock"
```

Add two private helpers:
```python
def _acquire_processing_lock():
    """Try to get exclusive lock. Returns open fd on success, None if already held."""

def _release_processing_lock(fd):
    """Release and close the fd returned by _acquire_processing_lock()."""
```

### 7.2 — Rewrite `structure_and_advance` to use the file lock

Replace the soft check-then-set with a hard exclusive lock:
1. Call `_acquire_processing_lock()` — returns `None` immediately if another process holds it → return `(False, None, True)`
2. Inside the lock: load fresh state; set `state["processing"] = True`; save
3. Remove the old `if fresh_state.get("processing"): return` soft check (lock replaces it)
4. In `finally`: clear `processing` flag from state; call `_release_processing_lock()`

The `state["processing"]` flag is kept as a **display signal** for the dashboard spinner — it does not do any locking itself anymore.

---

## Phase 6 — Clean Public API for `review_engine` (Priority: High)

Found by grepping all external callers of `review_engine._*` across the codebase.
Four files (dashboard, tray, morning_brief, evening_reminder) all reach into private internals.

### Root cause

`review_engine.py` was designed as an internal module. As dashboard, tray, morning_brief, and evening_reminder grew, they reached directly into `_` functions rather than a proper API being defined. Result: any internal rename breaks four files; callers mutate state bypassing the engine's own guards.

### Rule

- **State reads** (`_load_state`, `_load_streak`) → make public (read is always safe).
- **State writes** (`_save_state`, `_bust_brief_cache`) → stay private; only accessible via engine-owned operations.
- **Pure helpers** (`_fmt_duration`, `_extract_step_section`, etc.) → make public (no side effects).
- **Write-triggering operations** (`_run_context_brief`) → wrap in new public function `regenerate_brief()`.
- **`_rlog` shim** → keep at `_rlog` (voice_control, telegram_service depend on the name; changing it would be churn with zero benefit).

### 6.1 — Rename `_load_state` → `load_state`

State reading is always safe from outside. External callers: tray (4×), dashboard (7×).
Internal callers: many — use `replace_all=True`.

### 6.2 — Rename 8 read-only helpers to public names

| Old name | New public name | Internal callers? |
|---|---|---|
| `_fmt_duration` | `fmt_duration` | None |
| `_get_focus_word_counts` | `get_focus_word_counts` | `_get_weekly_focus_trend` |
| `_get_daily_note_path` | `get_daily_note_path` | Many (write_step_to_note, complete_review, etc.) |
| `_extract_evening_review_section` | `extract_evening_review_section` | `_read_last_n_notes` |
| `_extract_step_section` | `extract_step_section` | None |
| `_read_last_n_isolated_notes` | `get_isolated_notes` | None |
| `_mark_task_done` | `mark_task_done` | None |
| `_load_streak` | `load_streak` | `update_streak`, `initialize_review` |

Use `replace_all=True` for the four with internal callers.

### 6.3 — Add `regenerate_brief(script_dir, config)` public function

Encapsulates: `_bust_brief_cache` + clear state fields + `_save_state` + spawn `_run_context_brief` thread.
Dashboard `_regen_brief` reduces to 3 lines (set UI state, call engine).
`_save_state` stays private — dashboard stops touching it.

### 6.4 — Remove `self.is_processing` from `review_dashboard`

Same dual-flag pattern as Phase 5.1 (tray). `state["processing"]` is the sole guard.
`busy` in `_update_ui` and `_update_context_panel` becomes `state.get("processing", False)` only.
`_do_next` guard becomes: load state → check `state.get("processing")` → spawn thread (no local flag).

### 6.5 — Update all external callers to use public API

- `tray_app.py`: 4× `_load_state` → `load_state`
- `review_dashboard.py`: all private calls → public equivalents; `_regen_brief` → `regenerate_brief()`
- `morning_brief.py`: `_get_daily_note_path`, `_extract_evening_review_section`, `_extract_step_section` → public
- `evening_reminder.py`: `_load_streak` → `load_streak`

---

## Phase 5 — Post-Review Correctness Fixes (Priority: High)

Found during deep code review (2026-05-22). Three issues that survived Phases 1–4.

### 5.1 — Remove Surviving `self.is_processing` Dual Flag

**Problem**: `tray_app.py` still has `self.is_processing` (L42). Step 1.2 said to remove it — it wasn't. `next_step_review` sets it (L451) alongside `state["processing"]` in the file. Two sources of truth for the same concept.

**Fix**: Remove `self.is_processing` from `__init__`. Replace its single read in `next_step_review` with a check on the freshly-loaded state's `processing` flag. Remove its write in `_structure_and_advance` finally block. The `state["processing"]` in the file is the authoritative lock.

### 5.2 — Wire `FEATURES.direct_typing` and `FEATURES.clipboard_output` in `_run_normal_mode`

**Problem**: `tray_app.py:_run_normal_mode` checks `self.engine.config.get("DIRECT_TYPING")` (old flat key, always falsy now) and runs `xclip` unconditionally. The `FEATURES` block was added in Phase 3 but never wired in this method. Feature toggles exist in GUI but have no effect.

**Fix**: Replace the old `DIRECT_TYPING` check with `self.engine.config.get("FEATURES", {}).get("direct_typing", True)`. Wrap the `xclip` block with `if self.engine.config.get("FEATURES", {}).get("clipboard_output", True):`.

### 5.3 — Replace Private `_save_state` Call in `tray_app._handle_review_step`

**Problem**: `tray_app.py:328` calls `review_engine._save_state(self.review_state)` — a private function. Tray is doing raw state manipulation that belongs inside `review_engine`. Leaky abstraction.

**Fix**: Add a public function `review_engine.accumulate_clip(state, raw_text) -> state` that appends to `accumulated_raw`, sets `awaiting_more=True`, saves state, and returns the updated state. `_handle_review_step` calls this instead.

---

## Phase 10 — Final Hardening (Priority: Medium)

Three issues found by post-Phase-9 audit.

### 10.1 — Defensive guard inside `initialize_review()`

**Problem**: `initialize_review()` has no self-protection against being called while a review is active. `start_review()` has a re-entry guard (Phase 9.1), but `initialize_review()` is the actual state-overwrite function — if ever called from any other path it would clobber the live state and the in-progress context brief thread.

**Fix**: Add `is_review_active()` check at the top of `initialize_review()` and return early if True.

### 10.2 — `_do_next()` missing `active` guard

**Problem**: Phase 9.2 added `if not state.get("active", True): return` to `_do_skip()` and `_do_redo()` but `_do_next()` was missed. Inconsistent. `structure_and_advance()` does reload state from disk so double-completion is prevented, but the inconsistency leaves a gap in intent.

**Fix**: Add `if not state.get("active", True): return` to `_do_next()` immediately after the None check.

### 10.3 — Orphaned review audio routed to normal mode

**Problem**: In `_handle_review_step()`, if `fresh_state is None` (state file vanished mid-recording), the code calls `_run_normal_mode(raw_text)`. This processes review audio (e.g. "Step 2: achievements today") through the LLM refine pipeline and copies the result to clipboard. User may paste review content into the wrong context without realising.

**Fix**: Replace the `_run_normal_mode(raw_text)` fallback with a notification + discard. The audio is not recoverable as a valid review step, and treating it as general voice input is wrong.

---

## Phase 9 — Edge-Case Hardening (Priority: High)

Three narrow but real bugs found by post-Phase-8 deep audit.

### 9.1 — Guard `start_review()` against re-entry

**Problem**: `start_review()` has no code-level guard when `is_in_review=True`. Menu visibility (`_start_review_visible`) prevents normal users from hitting it, but the guard belongs in the function itself, not only in the menu.

**Risk**: If called while in review (programmatically, or if menu guard glitches): `initialize_review()` overwrites the state file, abandoning the current session, spawning a second watcher thread.

**Fix**: Add `if self.is_in_review: return` at the top of `start_review()`.

### 9.2 — Guard `_do_skip()` and `_do_redo()` against stale state

**Problem**: Dashboard `_do_skip()` and `_do_redo()` load state, then call `skip_step()` / `redo_step()` with that snapshot. If the review completes (state deleted) between the load and the call, `skip_step()` receives a stale dict and advances the step counter, potentially triggering `complete_review()` a second time (double summary, double narration).

**Risk**: Narrow window (Skip button is disabled during `processing=True`), but not zero.

**Fix**: After loading state, check `if not state.get("active", True): return` before calling the engine function. A completed/cancelled review has `"active": False` or no state file — both mean "do nothing".

### 9.3 — Guard `_handle_review_step()` against `review_config=None`

**Problem**: `run_full_process()` checks `if self.is_in_review:` then calls `_handle_review_step()`. Between that check and the call inside the thread, `cancel_review()` can run and set `self.review_config = None`. Inside `_handle_review_step()`, `get_current_step(fresh_state, self.review_config)` then receives `None` as config and crashes with `AttributeError`.

**Risk**: Exception is caught and shown as an error notification — not silent, but confusing to user.

**Fix**: At the top of `_handle_review_step()`, add `if self.review_config is None: return` guard.

---

## Phase 8 — Tray Completion Sync (Priority: High)

### Root Cause

When all steps complete via the **dashboard** (`review_engine.complete_review()` deletes the state file), the tray process is never notified. It keeps `is_in_review=True` and continues showing "Next Step / Skip / Redo" menu items. The tray only discovers completion if the user happens to click one of those items (which triggers `_load_review_state_or_finish()` → state gone → `_review_finished()`).

No IPC mechanism exists between the dashboard process and the tray process for completion events.

### Why This Breaks Modularity

The tray's UI state diverges from actual system state. A second review cannot start cleanly if the tray menu still shows review items. The tray icon stays green ("review" colour) even after the session is done.

### Fix: Background Completion Watcher Thread

Add `_watch_review_completion()` daemon thread to `VoiceAssistantTray`. Starts when a review begins (`start_review`). Polls `is_review_active()` every 2 seconds while `self.is_in_review` is True. When it detects the review is no longer active, calls `_review_finished()` to reset tray state and refresh the menu.

No new IPC, no new files, no new dependencies. Reuses the same `is_review_active()` call the dashboard already uses for its 500ms poll. The 2-second resolution is imperceptible to the user.

### 8.1 — Add `_watch_review_completion()` to `tray_app.py`

```python
def _watch_review_completion(self):
    while self.is_in_review and self.running:
        time.sleep(2)
        if not self.is_in_review:
            break
        active, _ = review_engine.is_review_active(self.script_dir)
        if not active:
            _tlog("_watch_review_completion: review no longer active — resetting tray")
            self._review_finished()
            break
```

### 8.2 — Start the watcher from `start_review()`

After setting `self.is_in_review = True`, start the daemon thread:

```python
threading.Thread(target=self._watch_review_completion, daemon=True).start()
```

---

## Phase 11 — Pending Task Story Engine (Priority: High)

Extends the morning brief from "read yesterday's list" into an intelligent task-age tracker. Scans the last N daily notes, identifies tasks that have been carried over without being checked off, and narrates a story grouped by how many days each task has been pending.

### Why N days is a parameter

`pending_task_lookback_days` defaults to **7** in `review_config.json`. Users can set it to 3, 5, 20 — any integer. The default of 7 means the system always has a full week of context. A user doing focused sprints might prefer 3; a user with longer-horizon work might want 14 or 20.

### 11.1 — Add config defaults

Add to `review_engine.py` default config and `review_config.json`:
```json
"pending_task_lookback_days": 7,
"pending_task_warn_threshold": 3,
"pending_task_critical_threshold": 5
```

`lookback_days` = how many past days to scan.
`warn_threshold` = days pending before ⚠️ tone in narration.
`critical_threshold` = days pending before 🚨 tone.

### 11.2 — Add `_parse_priority_tasks(text)` in `review_engine.py`

Parses a `### Tomorrow's Priorities` section and returns:
```python
[{"text": "Resolve field officer errors", "done": False}, ...]
```
- `- [ ] ...` → `done=False`
- `- [x] ...` → `done=True`
- Non-task lines (blank, headings) are skipped.

### 11.3 — Add `_normalize_task(text)` in `review_engine.py`

```python
def _normalize_task(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text
```

Used for cross-day matching. Two tasks are the same if their normalized forms are identical, or if one contains ≥70% of the other's words (handles LLM minor rephrasing).

### 11.4 — Add `get_pending_tasks(script_dir, config)` public function

Core logic:
1. Read `lookback_days` from config (default 7).
2. For each of the last `lookback_days` days (most recent first): extract `### Tomorrow's Priorities` from daily note; parse tasks.
3. Build a set of "done" tasks (normalized text of any `- [x]` seen on any day).
4. For each task in **yesterday's** priorities that is unchecked and not in the "done" set:
   - Walk forward through older days to find the earliest day it also appeared (unchecked) → `first_seen`.
   - `days_pending = (yesterday − first_seen).days + 1`
5. Return list of `{"text", "days_pending", "first_seen"}` sorted by `days_pending` descending.

Matching rule: normalized exact match first; then word-overlap ≥70%.

### 11.5 — Add `build_pending_story(pending_tasks, config)` in `review_engine.py`

Template-based (no LLM). Produces EN or HI text based on `context_brief_language`.

Group tasks into buckets:
- **Critical** (≥ `critical_threshold` days): prefix `🚨 N days pending`
- **Warning** (`warn_threshold` ≤ N < `critical_threshold`): prefix `⚠️ N days pending`
- **Recent** (2 days): prefix `📌 Since yesterday`
- **New** (1 day): prefix `🆕 New today`

Closing line: "Your oldest pending task is N days old — consider making it today's priority."
(Translated to Hindi if `context_brief_language == "hi"`.)

### 11.6 — Update `morning_brief.py`

In `run_morning_brief()`, after the existing priorities logic:
1. Call `pending = review_engine.get_pending_tasks(script_dir, config)`.
2. If pending tasks exist: call `review_engine.build_pending_story(pending, config)`.
3. Prepend the pending story to the narration and notification (pending story first, today's new tasks second).
4. Include pending count in the Telegram message.

Pending story is only added if `pending_task_lookback_days > 0` (allows opt-out by setting to 0).

### 11.7 — Expose in config GUI

In `config_gui.py` (Notifications tab), add:
- **Pending task lookback** — integer entry, default 7, label "Days to look back for pending tasks (0 = off)".

### 11.8 — Update docs

- README: new feature bullet + config table rows.
- `plan.md` notes: mark complete.
- `progress.md`: new rows for 11.1–11.8.

---

## Notes (Updated During Execution)

- 2026-05-26: **Code review complete (post-Phase-11).** Deep dive found: (1) `pending_task_warn_threshold` + `pending_task_critical_threshold` missing from config GUI save logic — fixed by adding two entry fields (rows 15–18) and wiring into `_save_all()`; (2) README features bullet updated to mention threshold configurability; (3) `progress.md` row 11.7 corrected. All Phases 1–11 now confirmed correct by review. Remaining architectural note: Notifications tab uses hardcoded row numbers — candidate for `current_row` auto-increment refactor in a future phase.
- 2026-05-26: **Phase 11 complete.** `_parse_priority_tasks`, `_normalize_task`, `_tasks_match`, `get_pending_tasks`, `build_pending_story` added to `review_engine.py`. `morning_brief.py` updated: pending story narrated first (emoji-free), then today's priorities; notification, Telegram, and state file all updated. Config GUI: `pending_task_lookback_days` entry in Notifications tab. Improvement over plan: `build_pending_story` returns `{"narration", "display"}` dict instead of plain string — keeps TTS clean. Overlap threshold set to 60% (not 70%) after finding singular/plural word forms ("officer"/"officers") cause false non-matches at 70%.
- 2026-05-26: **Phase 11 opened.** Pending Task Story Engine: scan last N (default 7, user-configurable) daily notes, find unchecked tasks that recur across days, narrate age-grouped story in morning brief. Config key `pending_task_lookback_days` controls lookback window; 0 disables the feature.
- 2026-05-22: Plan created. Previous plan (phases 1–5) archived to `docs/archive/`.
- 2026-05-22: **Phase 1 complete.** 1.1 done — `structure_and_advance()` added to `review_engine.py`; tray and dashboard reduced to thin wrappers. 1.2 resolved by 1.1 (no additional code needed). 1.3 done — `fcntl.flock` added. 1.4 done — text file at `/tmp/review_narration_last.txt`.
- 2026-05-22: **Phase 2 complete.** 2.1 — `theme.py` created, 4 files updated. 2.2 — `utils.get_logger()` added, shim pattern kept existing call sites working without mass replace. 2.3 — dead `run_pipeline()` deleted. 2.4 — already dynamic, no change.
- 2026-05-22: **Phase 3 complete.** 3.1 — `FEATURES` block added to `config.json` and `utils.py` defaults. 3.2 — new "⚙ Features" tab in config GUI. 3.3 — redo now truncates vault file at recorded byte offset; section_fill steps warn manually (in-place edits can't be simply truncated).
- 2026-05-22: **Phase 4 complete.** README updated with new files, config tables, corrected known issues. `progress.md` reflects all ✅.
- 2026-05-22: **Phase 6 complete.** 9 private helpers renamed to public names (load_state, fmt_duration, get_focus_word_counts, get_daily_note_path, extract_evening_review_section, extract_step_section, get_isolated_notes, mark_task_done, load_streak). `regenerate_brief()` added — dashboard no longer touches `_save_state`. `self.is_processing` removed from dashboard. Final grep: only `_rlog` shim survives across all files.
- 2026-05-23: **Phase 10 complete.** 10.1 — defensive `is_review_active()` guard added to `initialize_review()`. 10.2 — `active` guard added to `_do_next()` for consistency. 10.3 — orphaned review audio now discards with notification instead of routing to normal mode.
- 2026-05-23: **Phase 10 opened.** Post-Phase-9 audit: 3 issues — no self-guard in `initialize_review()`, missing `active` check in `_do_next()`, review audio falls back to normal mode when state vanishes.
- 2026-05-23: **Phase 9 complete.** 9.1 — `start_review()` re-entry guard added. 9.2 — `_do_skip`/`_do_redo` check `state.get("active", True)` before calling engine. 9.3 — `_handle_review_step` guards `review_config is None` at entry.
- 2026-05-23: **Phase 9 opened.** Post-Phase-8 deep audit found 3 narrow but real bugs: `start_review()` re-entry, stale-state double-completion in dashboard skip/redo, `review_config=None` crash race.
- 2026-05-22: **Phase 8 complete.** `_watch_review_completion()` daemon thread added to tray; started from `start_review()`. Polls every 2 s, calls `_review_finished()` when `is_review_active()` returns False. Idempotent — safe if another path clears `is_in_review` first.
- 2026-05-22: **Phase 8 opened.** Deep audit revealed tray never detects review completion triggered by dashboard — `is_in_review` stays True, menu items stay stale. Fix: 2-second watcher thread started at review begin, polls `is_review_active()`, calls `_review_finished()` when gone.
- 2026-05-22: **Phase 7 complete.** `_acquire_processing_lock()` / `_release_processing_lock()` added. `structure_and_advance` now acquires `LOCK_EX|LOCK_NB` before any state check — concurrent caller bails immediately. `state["processing"]` is display-only. `skip_step`/`redo_step` excluded from lock (same-process flock re-acquisition deadlocks on Linux — documented as accepted residual risk for double-skip only).
- 2026-05-22: **Phase 7 opened.** TOCTOU race in `structure_and_advance` identified. Fix: exclusive lock file (`/tmp/review_processing.lock`) acquired with `LOCK_NB` before check-then-set. `skip_step`/`redo_step` excluded from lock (same process re-acquisition deadlocks on Linux flock). Their callers' `state.get("processing")` checks remain sufficient protection.
- 2026-05-22: **Phase 6 opened.** Full grep of all external callers revealed private API violations across 4 files (dashboard, tray, morning_brief, evening_reminder). 9 functions need to become public; 1 new wrapper (`regenerate_brief`) needed; dashboard `self.is_processing` still present.
- 2026-05-22: **Phase 5 complete.** 5.1 — `self.is_processing` fully removed from tray; `state["processing"]` is sole lock. 5.2 — `clipboard_output` and `direct_typing` feature flags now wired in `_run_normal_mode`. 5.3 — `accumulate_clip()` public API added; tray no longer touches `_save_state` directly.
