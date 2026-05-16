# Interactive Evening Review — Development Plan

## Phase 1: Core Review Engine (MVP) ✅ Complete

### 1.1 Configuration
- `review_config.json` with all defaults externalized
- Vault paths, expiry, per-step flags (`isolate_file`, `skippable`, `refine`)
- Default steps: Focus Word, Achievements, Tomorrow's Priorities, Wellness Log

### 1.2 Review Engine (`review_engine.py`) ✅
- Full state machine: initialize, advance, skip, redo, cancel, complete
- State file: `/tmp/review_state.json`
- Append-only Obsidian writes with redo support
- Auto-expiry (1hr default), crash recovery on tray restart

### 1.3 Tray Integration (`tray_app.py`) ✅
- 4th icon state: green (review waiting)
- Dynamic menu: Skip / Redo / Cancel / Next Step
- `awaiting_more` pattern: manual advance, multi-recording per step
- SIGUSR1 hotkey bridge for Wayland compatibility
- Single static menu with dynamic callables (no menu rebuild needed)

---

## Phase 1.5: UX Refinements (Current Sprint)

### 1.5.1 Correct Daily Note Path
- **Format:** `~/learning_vault/My Daily Notes/YYYY/MonthName/YYYY-MM-DD.md`
- Example: `My Daily Notes/2026/May/2026-05-16.md`
- English full month names always (locale-independent)
- `os.makedirs(exist_ok=True)` for year/month folders automatically

### 1.5.2 Obsidian-Compatible Note Template
- If the daily note file does not exist, create it with full Obsidian template:
  ```
  ---
  creation date: YYYY-MM-DD
  modification date: Day DDth Month YYYY HH:MM:SS
  ---

  << [[YYYY-MM-DD -1]] | [[YYYY-MM-DD +1]] >>

  # YYYY-MM-DD

  ### Audio

  ### Meeting

  ### Movement

  ## Evening Review
  ```
- If file already exists (Obsidian created it): append `## Evening Review` section at the end (if not already present)
- Hardcoded template to start; config-based template in Phase 2

### 1.5.3 Per-Step LLM Structuring (Deferred Write Pattern)
- **New flow:** transcribe → accumulate raw text in state file → structure on "Next Step"
- State file gains `accumulated_raw: []` (list, one entry per recording for the current step)
- Each Ctrl+Alt+V: transcribe only → append to `accumulated_raw` → set `awaiting_more=True`
- "Next Step" click: combine `accumulated_raw` → run `structure_prompt` via LLM → write structured output to note → advance
- "Next Step" processing runs in background thread (icon → blue during structuring, green after)
- Per-step `structure_prompt` field in `review_config.json` (with `{raw_text}` placeholder)

**Default structure prompts:**

| Step | Output style |
|---|---|
| Focus Word | Extract single core focus word/theme only |
| Achievements | Bullet list, past-tense action verbs |
| Tomorrow's Priorities | `- [ ]` checkbox list |
| Meeting | Key decisions + action items as bullets |
| Movement | 1–2 line plain summary |
| Wellness Log | Raw, no LLM (`refine: false`) |

### 1.5.4 Meeting & Movement as Review Steps (Steps 5 & 6)
- Add Meeting and Movement to `review_steps` in `review_config.json`
- New flag: `section_fill: true` — instead of appending, finds existing `### Meeting` / `### Movement` header in the file and inserts content directly below it
- If section header not found: appends as normal
- Wellness isolation path updated to match new year/month folder structure

### 1.5.5 Voice Narration (espeak-ng)
- `"voice_narration": true` toggle in `review_config.json`
- `narrate(text, config)` function in `review_engine.py` using `subprocess.Popen` (non-blocking)
- Narration at key moments only:

| Trigger | Narration |
|---|---|
| Step starts | *"Step 2: Achievements. Please speak now."* |
| Recording stops | *"Processing."* |
| Step saved / awaiting | *"Saved. Speak more, or click Next Step."* |
| Next Step clicked | *"Moving to step 3."* |
| Step skipped | *"Step skipped."* |
| Review complete | *"Evening review complete."* |
| Review cancelled | *"Review cancelled."* |

- Plays alongside desktop notifications (not replacing them)
- `espeak-ng` already installed; Piper can be swapped in later by changing one function

---

## Phase 2: Intelligent Reflection (Future)

### 2.1 AI-Powered Contextual Questions
- Read last N days of Obsidian notes (configurable, default 1, range 1-7)
- LLM generates contextual follow-up questions prepended to step prompts

### 2.2 Config-Based Note Template
- `review_config.json` field: `daily_note_template` path
- User edits their own template file; system reads and fills placeholders

### 2.3 Desktop Launcher
- `EveningReview.desktop` for single-click launch from app drawer

### 2.4 Review History & Analytics
- Weekly/monthly summary generation
- Streak tracking

---

## Design Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| Trigger mechanism | GNOME shortcut → SIGUSR1 → tray | Wayland-compatible; no xbindkeys needed |
| Review mode indicator | Green tray icon (4th state) | Persistent visual signal |
| Abandonment handling | Auto-expiry (1hr default) + Cancel menu | Prevents permanent hotkey hijacking |
| Skip/Redo | Both supported | Redo physically deletes last entry for clean notes |
| Manual step advance | `awaiting_more` pattern + Next Step button | User controls when to move on |
| Multi-recording per step | Accumulate raw in state, structure on Next Step | One clean LLM pass per step |
| Step notification timing | Before recording (first press only) | No spam on continuation recordings |
| LLM structuring | Deferred to Next Step click, runs in background | Non-blocking; full context for structuring |
| Fill-in sections | Meeting/Movement use `section_fill: true` | Writes into existing Obsidian template sections |
| Daily note path | `YYYY/MonthName/YYYY-MM-DD.md` | Matches user's Obsidian vault structure |
| Note template | Hardcoded, Obsidian-compatible | Created only when file missing |
| Voice narration | espeak-ng, non-blocking, config toggle | Zero install cost; eyes-free UX |
| Menu architecture | Single static menu, dynamic callables | Reliable under Wayland/GTK pystray |
| Config philosophy | Everything configurable with sensible defaults | Core design principle |
