# Progress Tracker: Interactive Evening Review

## Phase 1 — Core Review Engine ✅ Complete

| Task | Status | Note |
| :--- | :--- | :--- |
| **Configuration** | | |
| Create `review_config.json` with default steps | ✅ | Focus Word, Achievements, Priorities, Wellness |
| Add `review_expiry_hours` (default: 1hr) | ✅ | Configurable |
| Add per-step flags: `isolate_file`, `skippable`, `refine` | ✅ | Configurable per step |
| Add vault path config (daily_notes, wellness_notes) | ✅ | Expandable `~` paths |
| **`review_engine.py`** | | |
| `is_review_active()` with expiry check | ✅ | Reads state file, checks timestamp |
| `initialize_review()` | ✅ | Creates state file, fires Step 1 notification |
| `get_current_step()` | ✅ | Returns current step dict from config |
| `append_to_note()` | ✅ | Append-only, template formatting, file isolation |
| `advance_step()` | ✅ | Increments index, fires next notification |
| `skip_step()` | ✅ | Advances without writing; writes `skip_default` to note if step defines one |
| `redo_step()` | ✅ | Removes last block from Markdown, re-prompts |
| `cancel_review()` | ✅ | Deletes state file, sends notification |
| `complete_review()` | ✅ | AI summary, prepend to daily note, cleanup |
| `check_startup_state()` | ✅ | Resume same-day or expire stale |
| `send_awaiting_notification()` | ✅ | Notifies user after save to speak more or advance |
| **`utils.py`** | | |
| Add `load_review_config()` helper | ✅ | Same merge pattern as existing load_config |
| **`engine.py`** | | |
| Review routing after refinement | ✅ | Route to Obsidian if review active |
| Step reminder notification before recording | ✅ | Only on first press (not continuations) |
| Skip LLM if step has `refine: false` | ✅ | Save raw text for wellness step |
| **`tray_app.py`** | | |
| Add green icon (4th state: review waiting) | ✅ | Color: #a6e3a1 |
| Single static menu with dynamic callables | ✅ | Reliable under Wayland/GTK |
| "Start Evening Review" menu item | ✅ | Visible only when review not active |
| "Next Step" menu item | ✅ | Visible only when `awaiting_more=True` |
| "Skip This Step" menu item | ✅ | Visible only when `awaiting_more=False` during review |
| "Redo This Step" menu item | ✅ | Visible only during review |
| "Cancel Review" menu item | ✅ | Visible only during review |
| Current step label in menu | ✅ | e.g. "Step 2/4: Achievements ✓ Saved" |
| `awaiting_more` pattern (multi-recording per step) | ✅ | Ctrl+Alt+V appends; Next Step advances |
| Startup state check (resume/expire) | ✅ | On tray boot |
| SIGUSR1 hotkey bridge for Wayland | ✅ | GNOME shortcut → pkill -USR1 → tray |

---

## Phase 1.5 — UX Refinements (Current Sprint)

| Task | Status | Note |
| :--- | :--- | :--- |
| **Step A: Path format** | | |
| Update `_get_daily_note_path()` to `YYYY/MonthName/YYYY-MM-DD.md` | ✅ | |
| Update `_get_wellness_note_path()` with same structure | ✅ | |
| Ensure `initialize_review()` creates year/month dirs | ✅ | |
| **Step B: Note template** | | |
| `_create_daily_note()` with full Obsidian-compatible template | ✅ | Frontmatter, nav links, Audio/Meeting/Movement/Evening Review |
| Append `## Evening Review` header if file exists but section missing | ✅ | `_ensure_evening_review_section()` |
| `_fill_section()` for section_fill steps | ✅ | Finds existing ### header, inserts content below it |
| **Step C: Deferred LLM structuring** | | |
| Add `accumulated_raw: []` to state file | ✅ | |
| Change recording flow: transcribe only → accumulate raw | ✅ | No LLM during recording |
| `_structure_and_advance()` background thread on Next Step | ✅ | Icon → blue during structuring |
| `write_step_to_note()` with `section_fill` support | ✅ | |
| Add `structure_prompt` defaults to all steps in `review_config.json` | ✅ | |
| Add `engine.refine_with_prompt()` method | ✅ | Takes a full prompt string directly |
| **Step D: Meeting & Movement steps** | | |
| Add Step 5 (Meeting) to `review_config.json` | ✅ | `section_fill: true` |
| Add Step 6 (Movement) to `review_config.json` | ✅ | `section_fill: true` |
| Implement `section_fill` write logic in `write_step_to_note()` | ✅ | |
| **Step E: Voice narration** | | |
| Add `narrate(text, config)` using `espeak-ng` (non-blocking) | ✅ | Silently skips if not installed |
| Add `"voice_narration": true` to `review_config.json` | ✅ | Config toggle |
| Wire narration at: step start, processing, saved, next, skip, complete, cancel | ✅ | |
| Piper neural TTS support | ✅ | `tts_engine: piper` + `piper_model` path; falls back to espeak if model missing |
| TTS engine selector in Settings GUI | ✅ | Dropdown + piper model path field; disables path field when espeak selected |

---

## Phase 1.6 — Context & Template

| Task | Status | Note |
| :--- | :--- | :--- |
| Config-based note template | ✅ | `templates/daily_note.md` + `templates/wellness_note.md`; `{{date}}`, `{{prev_day}}`, `{{next_day}}`, `{{mod_date}}` tokens; hardcoded fallback if file missing |
| `skip_default` field on steps | ✅ | Text written to note when step is skipped (Movement → "only office") |
| Past-date review support | ✅ | Date prompt on launch; `state["date"]` vs `state["started_at"]` separation |
| Read last N days of Obsidian notes | ✅ | `_read_last_n_notes()` extracts `## Evening Review` sections from last N daily notes |
| LLM synthesises context brief | ✅ | `_run_context_brief()` background thread: synthesised insight + nudge, narrated aloud then shown in dashboard |
| Dashboard context panel | ✅ | `📅 Context` panel shows "Analysing…" then brief text; polls `context_ready` from state |
| Per-step context (config toggle) | ✅ | `per_step_context: true` → context panel updates per step to show step-relevant history from past notes |
| Context Days + Per-step toggle in Settings GUI | ✅ | Settings → Evening Review → Review Behaviour |

---

## Phase 2 — Intelligent Reflection (Misc)

| Task | Status | Note |
| :--- | :--- | :--- |
| LLM generates contextual follow-up questions | 📅 | Injected into step prompts based on past-note patterns |
| Desktop launcher (`EveningReview.desktop`) | ✅ | `install_desktop.sh` — installs both tray + review launchers to `~/.local/share/applications/` |
| Weekly/monthly summary generation | 📅 | |

---

## Phase 3 — Bilingual Context Brief + Narration Controls ⏳ Current

### Decisions locked
- Single model → one Ollama call returning both EN + HI. Two models → two parallel calls.
- Cache key = date only. Regenerate button busts today's cache.
- Stop/Replay is universal (works for any narration, not just brief).
- Hotkeys `Ctrl+Alt+S` (stop) / `Ctrl+Alt+R` (replay) — always registered, no-op outside review.
- Voice wake-word control wired architecturally but shipped as Phase 8.

### 3A — Interruptible Narration Core
| Task | Status | Note |
| :--- | :--- | :--- |
| Add `_active_narration_proc` module-level var to `review_engine.py` | ✅ | Stores running piper/paplay process |
| `stop_narration()` — kills `_active_narration_proc` cleanly | ✅ | Safe if proc already done |
| `_last_narration_text` — stores last spoken text for replay | ✅ | Module-level, updated on every `narrate()` call |
| `replay_narration(config)` — re-narrates `_last_narration_text` | ✅ | Calls `narrate()` non-blocking |
| Wire `_active_narration_proc` into `_narrate_piper()` and `_narrate_espeak()` | ✅ | Both engines update the ref |

### 3B — Global Hotkeys
| Task | Status | Note |
| :--- | :--- | :--- |
| Register `Ctrl+Alt+S` → `stop_narration()` in `tray_app.py` | ✅ | Always-on via pynput, no-op outside review |
| Register `Ctrl+Alt+R` → `replay_narration(config)` in `tray_app.py` | ✅ | Always-on via pynput |

### 3C — Dual-Language Brief Generation
| Task | Status | Note |
| :--- | :--- | :--- |
| Add `brief_model`, `brief_model_en`, `brief_model_hi` to config defaults | ✅ | Single model = one call; two models = parallel calls |
| Update `_run_context_brief()` prompt to return `EN:` and `HI:` blocks | ✅ | Single-call path via `_call_brief_single()` |
| Add parallel two-call path when `brief_model_en` ≠ `brief_model_hi` | ✅ | `_call_brief_parallel()` — two threads, merged result |
| Parse and store `context_brief_en` + `context_brief_hi` in state | ✅ | Both saved to state file |
| Add `context_brief_language` config key (`"en"` or `"hi"`) | ✅ | Selects which language to narrate and display |
| Narrate the configured language brief | ✅ | `_run_context_brief()` picks from state |

### 3D — Brief Cache
| Task | Status | Note |
| :--- | :--- | :--- |
| `brief_cache.json` in project root — keyed by date | ✅ | `{"2026-05-18": {"en": "...", "hi": "...", "generated_at": "..."}}` |
| `_load_brief_cache(date_str)` — returns cached dict or None | ✅ | |
| `_save_brief_cache(date_str, en, hi)` — writes to cache file | ✅ | |
| Auto-prune keys older than 7 days on save | ✅ | Prevent bloat |
| `_run_context_brief()` checks cache before calling Ollama | ✅ | Cache hit → skip LLM entirely |

### 3E — Dashboard Controls
| Task | Status | Note |
| :--- | :--- | :--- |
| Add `⏹ Stop` button to context panel header in `review_dashboard.py` | ✅ | Calls `review_engine.stop_narration()` |
| Add `🔁 Replay` button to context panel header | ✅ | Calls `review_engine.replay_narration(config)` |
| Add `↺ Regenerate` button to context panel header | ✅ | Busts today's cache, re-runs `_run_context_brief()` |
| Extend stats label: `"3 days · 18 May 2026 · qwen2.5:3b"` | ✅ | Shows n days, date, model used |
| Show brief in `context_brief_language` language | ✅ | Dashboard reads `context_brief_en` or `context_brief_hi` from state |
| Two-column dashboard layout | ✅ | Left: steps + buttons; Right: context sidebar (auto-switches per step) |
| EN/HI toggle buttons in context sidebar | ✅ | Runtime language switch; re-renders brief + narrates chosen language |

### 3F — Settings GUI
| Task | Status | Note |
| :--- | :--- | :--- |
| Add "Brief Language" dropdown (`en` / `hi`) to config GUI | ✅ | `context_brief_language` |
| Add "Brief Model" field (single model mode) | ✅ | `brief_model` — defaults to structure model if blank |
| Add "Brief Model EN" + "Brief Model HI" fields (two-model mode) | ✅ | Shown when user picks "Two Models" |
| Dropdown toggle: "Single Model" / "Two Models" — show/hide fields accordingly | ✅ | `_on_brief_mode_change()` |
| Save all new keys to `review_config.json` | ✅ | Cleans up unused keys on mode switch |

---

## Phase 4 — Carry-Forward Unfinished Tasks ✅ Complete

| Task | Status | Note |
| :--- | :--- | :--- |
| `_read_unchecked_tasks(script_dir, config, date_str)` — parse `- [ ]` from previous day's vault note | ✅ | Returns list of strings; called at `initialize_review()` |
| `_mark_task_done(script_dir, config, task_text, note_date_str)` — writes `- [x]` to vault | ✅ | Returns bool; called from dashboard checkbox |
| Save tasks + `carryforward_date` to state at review start | ✅ | Fast — file parse only, no LLM |
| Narrate pending tasks at carry-forward step before step prompt | ✅ | *"कल के ये काम अभी बाकी हैं..."* blocking narration |
| Config toggle `"carryforward_tasks": true` + `"carryforward_step_id": 3` | ✅ | Configurable which step shows tasks |
| Dashboard right panel: interactive checkboxes at carry-forward step | ✅ | Clicking marks `- [x]` in vault; fails gracefully with warning |
| Settings GUI toggle for carry-forward | 📅 | Can be toggled via review_config.json for now |

---

## Phase 5 — Morning Priority Briefing ✅ Complete

| Task | Status | Note |
| :--- | :--- | :--- |
| `morning_brief.py` — reads yesterday's Priorities section from vault | ✅ | Parses `### Tomorrow's Priorities` via existing `_extract_step_section()` |
| Narrate priorities in configured language via Piper | ✅ | Same `review_engine.narrate()` TTS stack; intro in EN or HI per `context_brief_language` |
| Systemd user timer at configurable time | ✅ | `install_morning_brief.sh` — generates `.service` + `.timer` from `morning_briefing_time` |
| Config: `morning_briefing_enabled`, `morning_briefing_time` | ✅ | Both in `review_config.json` + engine defaults |
| Brief state saved to `/tmp/morning_brief_state.json` | ✅ | Includes `text`, `date`, `generated_at`; expires when date ≠ yesterday |
| "🌅 Replay Morning Brief" tray menu item | ✅ | Visible when valid state exists; narrates via `replay_morning_brief()` |
| Settings GUI fields for enable toggle + time picker | 📅 | Can be toggled via review_config.json for now |

---

## Phase 6 — Streak Tracker ✅ Complete

| Task | Status | Note |
| :--- | :--- | :--- |
| `streak.json` — stores `{"current": 12, "last_date": "2026-05-18", "best": 30}` | ✅ | `_load_streak` / `_save_streak` helpers |
| `update_streak()` — called at `complete_review()` | ✅ | Increments or resets based on last_date; idempotent for same-day double-call |
| Narrate streak at review start: *"आपकी लगातार N दिनों की streak है!"* | ✅ | Blocking narration after context brief |
| Milestone messages at 7, 14, 30, 100 days | ✅ | `_STREAK_MILESTONES` dict; narrated on `complete_review()` |
| Show streak in dashboard header | ✅ | `🔥 N` label; hidden when streak=0 |
| Config toggle `"show_streak": true` | ✅ | Disables all streak features when false |

---

## Phase 7 — Focus Word Trend ✅ Complete

| Task | Status | Note |
| :--- | :--- | :--- |
| Append focus word + date to `focus_words.jsonl` after step 1 saves | ✅ | `{"date": "2026-05-18", "word": "learning"}`; hooked in `write_step_to_note()` |
| Weekly scan (Sunday) — find most frequent word in last 7 entries | ✅ | `_get_weekly_focus_trend()` — `collections.Counter` on last 7 entries |
| Narrate trend at review start on Sundays | ✅ | Blocking narration in `_run_context_brief()` after streak; skipped if count < 2 |
| Config toggle `"focus_word_trend": true` | ✅ | Disables both tracking and narration when false |
| Simple frequency chart in dashboard (optional) | 📅 | Deferred — nice-to-have, not blocking |

---

## Phase 8 — Voice Wake-Word Control (Futuristic)

| Task | Status | Note |
| :--- | :--- | :--- |
| Evaluate `openwakeword` — offline, pip-installable, custom phrases | 📅 | Needs mic conflict testing with active TTS |
| Background listener thread during narration | 📅 | Detects "रुको"/"stop" → `stop_narration()`, "फिर से"/"again" → `replay_narration()` |
| VAD energy threshold to reject TTS bleed into mic | 📅 | |
| Config flag `"voice_control": false` — opt-in | 📅 | |
| Wire to same `stop_narration()` / `replay_narration()` as hotkeys | 📅 | No new engine code needed — just a new trigger |

---

### Legend
- ✅ **Complete**
- ⏳ **In Progress**
- 📅 **Planned**
- ❌ **Blocked**
