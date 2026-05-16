# Interactive Evening Review — Implementation Steps

## Phase 1 Steps (Complete) ✅

Steps 1–5 (config, engine, utils, engine.py, tray_app.py) are implemented and working.
See `progress_tracker.md` for full task status.

---

## Phase 1.5 Steps (Current Sprint)

---

### Step A: Fix Daily Note Path (`review_engine.py`)

Update `_get_daily_note_path()` and `_get_wellness_note_path()`:

```python
def _get_daily_note_path(script_dir, config, date_str=None):
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    dt = datetime.date.fromisoformat(date_str)
    year = dt.strftime("%Y")
    month = dt.strftime("%B")          # Full English month name: January, February...
    vault_paths = config.get("vault_paths", {})
    daily_notes_base = os.path.expanduser(vault_paths.get("daily_notes", "~/learning_vault/My Daily Notes"))
    return os.path.join(daily_notes_base, year, month, f"{date_str}.md")
```

Wellness path follows the same year/month pattern under the wellness subfolder.

Also update `initialize_review()` to create the year/month directory structure with `os.makedirs(exist_ok=True)`.

---

### Step B: Obsidian-Compatible Note Template (`review_engine.py`)

Replace the bare header creation in `append_to_note()` and `complete_review()` with a full template writer.

New helper function `_create_daily_note(file_path, date_str)`:

```python
def _create_daily_note(file_path, date_str):
    dt = datetime.date.fromisoformat(date_str)
    prev_day = (dt - datetime.timedelta(days=1)).isoformat()
    next_day = (dt + datetime.timedelta(days=1)).isoformat()
    now_str = datetime.datetime.now().strftime("%A %dth %B %Y %H:%M:%S")
    content = f"""---
creation date: {date_str}
modification date: {now_str}
---

<< [[{prev_day}]] | [[{next_day}]] >>

# {date_str}

### Audio

### Meeting

### Movement

## Evening Review

"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
```

Logic in `append_to_note()`:
- If file does not exist → call `_create_daily_note()`
- If file exists but `## Evening Review` section is absent → append `\n## Evening Review\n\n`
- Then append the step block

---

### Step C: Per-Step LLM Structuring + Deferred Write (`review_engine.py`, `tray_app.py`)

#### C1: State file gains `accumulated_raw`
```json
{
  "active": true,
  "current_step_index": 0,
  "accumulated_raw": [],
  "awaiting_more": false,
  ...
}
```

#### C2: Recording flow change (`tray_app.py` — `_handle_review_step`)
- **Remove** the `engine.refine()` call during recording
- Instead: append `raw_text` to `state["accumulated_raw"]`
- Save state, set `awaiting_more=True`, notify user, update menu
- No Obsidian write happens during recording

#### C3: "Next Step" triggers structuring (`tray_app.py` — `next_step_review`)
```python
def next_step_review(self, icon=None, item=None):
    # ... reload state ...
    # Run structuring in background thread so menu stays responsive
    threading.Thread(target=self._structure_and_advance, args=(state,), daemon=True).start()

def _structure_and_advance(self, state):
    self.update_icon("processing")
    step = review_engine.get_current_step(state, self.review_config)
    raw_combined = " ".join(state.get("accumulated_raw", []))
    
    if step.get("refine", True) and raw_combined.strip():
        structure_prompt = step.get("structure_prompt", "Reformat this as clear bullet points:\n{raw_text}")
        prompt = structure_prompt.replace("{raw_text}", raw_combined)
        # call Ollama with structure_prompt
        structured_text = self.engine.refine_with_prompt(prompt)
    else:
        structured_text = raw_combined
    
    review_engine.write_step_to_note(self.script_dir, self.review_config, step, structured_text, state)
    state["accumulated_raw"] = []
    state["awaiting_more"] = False
    review_engine.advance_step(self.script_dir, state, self.review_config)
    # update icon, check still_active, update menu
```

#### C4: Add `write_step_to_note()` to `review_engine.py`
- For steps with `section_fill: true`: find the `### SectionName` header in the file, insert content below it (before the next `###`)
- For all other steps: append block below `## Evening Review`

#### C5: Add `structure_prompt` defaults to `review_config.json`
```json
{
  "step_id": 2,
  "section_name": "Achievements",
  "structure_prompt": "Convert this voice note into a concise bullet-point list of achievements. Each bullet starts with a past-tense action verb. Output only the bullets:\n{raw_text}",
  ...
}
```

---

### Step D: Add Meeting & Movement as Steps 5 & 6 (`review_config.json`)

```json
{
  "step_id": 5,
  "section_name": "Meeting",
  "prompt_notification": "Step 5/6: Summarise today's meetings — decisions made and actions assigned.",
  "section_fill": true,
  "isolate_file": false,
  "skippable": true,
  "refine": true,
  "structure_prompt": "Summarise this meeting note into structured bullet points covering key decisions and action items. Use sub-bullets for actions:\n{raw_text}"
},
{
  "step_id": 6,
  "section_name": "Movement",
  "prompt_notification": "Step 6/6: Any movement, exercise or physical activity today?",
  "section_fill": true,
  "isolate_file": false,
  "skippable": true,
  "refine": true,
  "structure_prompt": "Summarise this movement/activity note in 1-2 plain sentences:\n{raw_text}"
}
```

The `section_fill: true` flag tells `write_step_to_note()` to insert content into the existing `### Meeting` / `### Movement` section rather than appending below `## Evening Review`.

---

### Step E: Voice Narration (`review_engine.py`, `tray_app.py`)

#### E1: Add `narrate()` to `review_engine.py`
```python
def narrate(text, config):
    if not config.get("voice_narration", True):
        return
    try:
        subprocess.Popen(
            ["espeak-ng", "-s", "140", "-a", "80", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass  # espeak-ng not installed, silently skip
```

#### E2: Add `"voice_narration": true` to `review_config.json`

#### E3: Narration call points (all non-blocking):

| Location | Call |
|---|---|
| `send_step_notification()` | `narrate(f"Step {idx+1}: {step_name}. Please speak now.", config)` |
| `run_full_process()` after recording stops | `narrate("Processing.", config)` |
| `send_awaiting_notification()` | `narrate("Saved. Speak more, or click Next Step.", config)` |
| `next_step_review()` before advance | `narrate(f"Moving to step {next_idx}.", config)` |
| `skip_step()` | `narrate("Step skipped.", config)` |
| `complete_review()` | `narrate("Evening review complete.", config)` |
| `cancel_review()` | `narrate("Review cancelled.", config)` |

---

### Step F: Update `progress_tracker.md`

Mark Phase 1.5 tasks as complete as they are implemented.

---

## Phase 2 Steps (Future)

- Config-based note template (user edits their own `.md` template file)
- AI contextual questions from last N days of notes
- Desktop launcher (`EveningReview.desktop`)
- Review streak tracking and weekly summaries
