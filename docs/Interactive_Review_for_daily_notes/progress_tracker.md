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
| `skip_step()` | ✅ | Advances without writing |
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
| Update `_get_daily_note_path()` to `YYYY/MonthName/YYYY-MM-DD.md` | 📅 | |
| Update `_get_wellness_note_path()` with same structure | 📅 | |
| Ensure `initialize_review()` creates year/month dirs | 📅 | |
| **Step B: Note template** | | |
| `_create_daily_note()` with full Obsidian-compatible template | 📅 | Frontmatter, nav links, Audio/Meeting/Movement sections |
| Append `## Evening Review` header if file exists but section missing | 📅 | |
| **Step C: Deferred LLM structuring** | | |
| Add `accumulated_raw: []` to state file | 📅 | |
| Change recording flow: transcribe only → accumulate raw | 📅 | No LLM during recording |
| `_structure_and_advance()` background thread on Next Step | 📅 | Icon → blue during structuring |
| `write_step_to_note()` with `section_fill` support | 📅 | Find header, insert below |
| Add `structure_prompt` defaults to all steps in `review_config.json` | 📅 | |
| Add `engine.refine_with_prompt()` method | 📅 | Takes a full prompt string directly |
| **Step D: Meeting & Movement steps** | | |
| Add Step 5 (Meeting) to `review_config.json` | 📅 | `section_fill: true` |
| Add Step 6 (Movement) to `review_config.json` | 📅 | `section_fill: true` |
| Implement `section_fill` write logic in `write_step_to_note()` | 📅 | |
| **Step E: Voice narration** | | |
| Add `narrate(text, config)` using `espeak-ng` (non-blocking) | 📅 | |
| Add `"voice_narration": true` to `review_config.json` | 📅 | Config toggle |
| Wire narration at: step start, processing, saved, next, skip, complete, cancel | 📅 | |

---

## Phase 2 — Intelligent Reflection (Future)

| Task | Status | Note |
| :--- | :--- | :--- |
| Read last N days of Obsidian notes | 📅 | N configurable, default 1, range 1-7 |
| LLM generates contextual follow-up questions | 📅 | Prepended to step prompts |
| Config-based note template | 📅 | User edits their own `.md` template file |
| Desktop launcher (`EveningReview.desktop`) | 📅 | Single-click from app drawer |
| Review history & streak tracking | 📅 | |
| Weekly/monthly summary generation | 📅 | |

---

### Legend
- ✅ **Complete**
- ⏳ **In Progress**
- 📅 **Planned**
- ❌ **Blocked**
