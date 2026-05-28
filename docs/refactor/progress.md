# Progress Tracker: Refactoring

> Last updated: 2026-05-26 (Phase 11 complete — Pending Task Story Engine)

| # | Task | Phase | Status | Notes |
|---|------|-------|--------|-------|
| 1.1 | Consolidate `_structure_and_advance` into `review_engine` | 1 — Bug Fixes | ✅ Complete | New `review_engine.structure_and_advance()`. Both tray and dashboard are thin wrappers. |
| 1.2 | Single `is_processing` source of truth | 1 — Bug Fixes | ✅ Complete | Resolved by 1.1. `state["processing"]` is cross-process truth; in-memory flags are UI guards only. |
| 1.3 | File lock on state writes | 1 — Bug Fixes | ✅ Complete | `fcntl.flock` in `_save_state()` (LOCK_EX) and `_load_state()` (LOCK_SH). 3-retry hack removed. |
| 1.4 | Narration replay across processes | 1 — Bug Fixes | ✅ Complete | `narrate()` writes to `/tmp/review_narration_last.txt`. `replay_narration()` reads file first. |
| 2.1 | Shared theme constants (`theme.py`) | 2 — Cleanup | ✅ Complete | Created `theme.py`. All 4 GUI files import from it. `config_gui.py` keeps `ERROR = RED` alias. |
| 2.2 | Shared logger via `utils.get_logger()` | 2 — Cleanup | ✅ Complete | `get_logger(name, log_file)` added to utils. Shim pattern: `_rlog`/`_tlog` delegate to Python logger. |
| 2.3 | Delete `engine.run_pipeline()` dead code | 2 — Cleanup | ✅ Complete | Deleted. Referenced non-existent `review_engine.append_to_note()`. No callers existed. |
| 2.4 | Dynamic review steps in config GUI | 2 — Cleanup | ✅ Complete | Already implemented — iterates `review_config["steps"]`. No change needed. |
| 3.1 | Feature flags in `config.json` | 3 — Config | ✅ Complete | `FEATURES` block in `config.json` + defaults in `utils.load_config()`. Wired to sounds and tray menu. |
| 3.2 | Feature toggles tab in config GUI | 3 — Config | ✅ Complete | New "⚙ Features" tab with `CTkSwitch` per feature. Written to `FEATURES` block on save. |
| 3.3 | Redo fully reversible | 3 — Config | ✅ Complete | `write_step_to_note` records byte `offset`; `redo_step` truncates file at that position. `section_fill` steps notify manually. |
| 4.1 | Update README.md | 4 — Docs | ✅ Complete | Added `theme.py`, updated config tables, fixed known-issues entry, updated docs index. |
| 4.2 | Update plan.md with learnings | 4 — Docs | ✅ Complete | This file. `plan.md` updated with completion notes. |
| 5.1 | Remove `self.is_processing` dual flag from tray | 5 — Correctness | ✅ Complete | Removed from `__init__`, `run_full_process`, `next_step_review`, `_structure_and_advance`, `_review_finished`. `state["processing"]` is now the sole lock. |
| 5.2 | Wire `FEATURES.direct_typing` / `clipboard_output` in `_run_normal_mode` | 5 — Correctness | ✅ Complete | `clipboard_output` gates xclip/xsel; `direct_typing` replaces old `DIRECT_TYPING` key. |
| 5.3 | Public `accumulate_clip()` API in `review_engine` | 5 — Correctness | ✅ Complete | New `review_engine.accumulate_clip(state, raw_text)`. Tray no longer calls `_save_state` directly. |
| 6.1 | Rename `_load_state` → `load_state` | 6 — Public API | ✅ Complete | State reader is always safe to expose; internal callers updated via replace_all. |
| 6.2 | Rename 8 private helpers to public names | 6 — Public API | ✅ Complete | `fmt_duration`, `get_focus_word_counts`, `get_daily_note_path`, `extract_evening_review_section`, `extract_step_section`, `get_isolated_notes`, `mark_task_done`, `load_streak`. |
| 6.3 | Add `regenerate_brief(script_dir, config)` | 6 — Public API | ✅ Complete | Encapsulates bust-cache + state clear + save + thread launch. Dashboard stops touching `_save_state`. |
| 6.4 | Remove `self.is_processing` from dashboard | 6 — Public API | ✅ Complete | Same dual-flag pattern as Phase 5.1. `state["processing"]` is sole guard. |
| 6.5 | Update all external callers to public API | 6 — Public API | ✅ Complete | tray (4×), dashboard (many), morning_brief (3×), evening_reminder (1×). |
| 6.6 | Final grep verification — zero private calls remain | 6 — Public API | ✅ Complete | Only `_rlog` shim should survive. |
| 7.1 | Add `_PROCESSING_LOCK_PATH` + `_acquire/release_processing_lock()` | 7 — TOCTOU Fix | ✅ Complete | Exclusive lock file at `/tmp/review_processing.lock`. LOCK_NB so concurrent caller bails immediately. |
| 7.2 | Rewrite `structure_and_advance` to use file lock | 7 — TOCTOU Fix | ✅ Complete | Lock replaces soft check-then-set. `state["processing"]` is display-only. `_processing_set` tracks cleanup. |
| 7.3 | Verification: lock flow correct, no deadlock with `skip_step` | 7 — TOCTOU Fix | ✅ Complete | `_acquire_processing_lock` called in exactly 1 place. `skip_step`/`redo_step` untouched. |
| 8.1 | Add `_watch_review_completion()` daemon thread to `tray_app.py` | 8 — Tray Sync | ✅ Complete | 2-second poll, calls `_review_finished()` when `is_review_active()` returns False |
| 8.2 | Start watcher from `start_review()` | 8 — Tray Sync | ✅ Complete | One daemon thread per review session; started after `is_in_review = True` |
| 8.3 | Verify idempotency and no double-call | 8 — Tray Sync | ✅ Complete | Loop condition `while self.is_in_review` exits naturally if another path already called `_review_finished()` |
| 8.4 | Update README Known Issues + plan notes | 8 — Tray Sync | ✅ Complete | README entry added; plan.md notes updated |
| 9.1 | Guard `start_review()` against re-entry | 9 — Hardening | ✅ Complete | `if self.is_in_review: return` at function entry |
| 9.2 | Guard `_do_skip`/`_do_redo` against stale state | 9 — Hardening | ✅ Complete | `if not state.get("active", True): return` before calling engine |
| 9.3 | Guard `_handle_review_step` against `review_config=None` | 9 — Hardening | ✅ Complete | `if self.review_config is None: return` at function entry |
| 9.4 | Verification + docs | 9 — Hardening | ✅ Complete | Syntax clean; plan.md and progress.md updated |
| 10.1 | Defensive guard in `initialize_review()` | 10 — Final Hardening | ✅ Complete | `is_review_active()` checked before any state write; returns early if active |
| 10.2 | `active` guard in `_do_next()` | 10 — Final Hardening | ✅ Complete | All three `_do_next/skip/redo` now share identical guard pattern |
| 10.3 | Discard orphaned review audio | 10 — Final Hardening | ✅ Complete | Notify + discard; `_run_normal_mode` no longer called from `_handle_review_step` |
| 10.4 | Verification + docs | 10 — Final Hardening | ✅ Complete | Syntax clean; grep confirmed; plan.md updated |

| 11.1 | Add `pending_task_lookback_days` / `warn_threshold` / `critical_threshold` to config | 11 — Pending Story | ✅ Complete | Default 7 days; 0 disables feature; added to `review_engine.py` defaults + `review_config.json` |
| 11.2 | Add `_parse_priority_tasks(text)` in `review_engine.py` | 11 — Pending Story | ✅ Complete | Parses `- [ ]` / `- [x]` lines; skips prose/headings silently |
| 11.3 | Add `_normalize_task(text)` + `_tasks_match(a, b)` | 11 — Pending Story | ✅ Complete | Word-overlap ≥ 60% (lowered from 70% — better handles singular/plural differences) |
| 11.4 | Add `get_pending_tasks(script_dir, config)` public function | 11 — Pending Story | ✅ Complete | Scans last N days; missing notes skipped (no break); present-note-no-task breaks chain |
| 11.5 | Add `build_pending_story(pending_tasks, config)` | 11 — Pending Story | ✅ Complete | Returns `{"narration": str, "display": str}`; narration is emoji-free for TTS |
| 11.6 | Update `morning_brief.py` to narrate pending story | 11 — Pending Story | ✅ Complete | Pending story before today's tasks; Telegram + notification + state all updated |
| 11.7 | Expose all three `pending_task_*` keys in config GUI | 11 — Pending Story | ✅ Complete | `lookback_days` (rows 13–14), `warn_threshold` (rows 15–16), `critical_threshold` (rows 17–18) in Notifications tab; all three wired into save; gap found+fixed in code review |
| 11.8 | Verification + docs (README, plan.md, progress.md) | 11 — Pending Story | ✅ Complete | All edge cases tested; 6/6 assertions pass |

---

### Legend
- ✅ Complete
- 🔧 In Progress
- ✅ Complete
- ❌ Blocked

---

### Completed Log

- **2026-05-22**: All 13 tasks completed in one session. Phases 1–4 done.
