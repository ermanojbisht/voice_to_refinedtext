# AI Voice Refiner

A **100% local, privacy-first** voice-to-text assistant for Ubuntu. Speak in English or Hindi — the system transcribes with Whisper, refines with a local LLM via Ollama, and delivers polished text to your clipboard. No cloud, no subscriptions, no data leaving your machine.

Built on top of this core, the **Evening Review** feature turns daily voice recordings into structured Obsidian notes — running a guided, step-by-step reflection session every evening with full LLM structuring per step.

---

## Features

### Core Voice Refiner
- **Offline speech-to-text** via `faster-whisper` (large-v3-turbo by default)
- **Local LLM refinement** via Ollama — grammar cleanup, professional rewriting
- **Bilingual** — auto-detects English vs Hindi, applies language-specific models and prompts
- **Silence-based auto-stop** — no fixed timer; recording ends naturally when you pause
- **Auto-clipboard** — refined text lands in your clipboard instantly
- **Direct typing mode** — optionally simulates keyboard input to insert text at cursor
- **Refine / Translate toggle** — switch between refining in the same language or translating Hindi → English
- **Audio feedback** — distinct chimes for recording start, end, and completion
- **System tray** — persistent coloured-dot indicator (grey/red/blue/green) with right-click menu

### Evening Review
- **Guided multi-step review** — configurable steps (Focus Word, Achievements, Priorities, Wellness, Meeting, Movement)
- **Accumulate multiple clips per step** — record, speak more, then advance when ready
- **Per-step LLM structuring** — each step has its own prompt template (bullet points, checkboxes, summaries)
- **Obsidian-compatible daily notes** — writes to `YYYY/MonthName/YYYY-MM-DD.md` with full YAML frontmatter and nav links
- **Section-fill mode** — Meeting and Movement fill existing `### Header` blocks; other steps append under `## Evening Review`
- **Isolated wellness notes** — Wellness step writes to a separate file
- **Voice narration** — speaks each step prompt aloud; supports **piper** (neural, natural-sounding, offline) or **espeak-ng** (built-in fallback); switchable in Settings
- **Last-N-days context brief** — at review start, reads the last N daily notes, synthesises them with an AI, narrates the brief aloud, and shows it in the dashboard context panel; helps you see patterns and decide what to focus on today
- **Per-step context** (optional) — shows step-relevant history from past notes in the context panel as each step becomes active
- **Streak tracker** — counts consecutive days of completed reviews; shown in the dashboard header (🔥 N); milestone narrations at 7 / 14 / 30 / 100 days; persisted in `streak.json`
- **Focus word trend** — records each day's focus word to `focus_words.jsonl`; on Sundays narrates the most-repeated word from the past 7 entries ("इस हफ्ते आपका सबसे ज़्यादा ध्यान … पर रहा।")
- **Telegram mobile notifications** — sends review-complete summary (with streak) and morning brief to your phone via a Telegram bot; configured in Settings → Notifications; powered by self-contained `telegram_service.py`
- **Morning priority briefing** — a systemd user timer runs `morning_brief.py` at a configured time; reads yesterday's Tomorrow's Priorities, sends a desktop notification + Telegram message, and narrates the list aloud; tray shows **Replay Morning Brief** while the state is fresh
- **Customisable daily note template** — edit `templates/daily_note.md` with `{{date}}`, `{{prev_day}}`, `{{next_day}}`, `{{mod_date}}` tokens; no code changes needed
- **Skip defaults** — skipping a step with a configured default (e.g. Movement → `only office`) writes that default to the note automatically
- **Live dashboard** — customtkinter window showing all steps, context panel, status icons, progress bar, streak label, and control buttons
- **AI end-of-review summary** — appends a 2-3 sentence AI-generated summary to the daily note on completion
- **After-midnight safe** — sessions started before midnight write to the correct date
- **Past-date reviews** — start a review for any past date via the date prompt on launch

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Trigger Layer                      │
│   Hotkey (Ctrl+Alt+V / GNOME shortcut)              │
│   Tray Menu  ·  Main GUI  ·  Dashboard buttons      │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                   tray_app.py                        │
│   State machine · Menu · Icon · SIGUSR1 handler      │
│   Replay Morning Brief                               │
└────────┬──────────────┬───────────────┬─────────────┘
         │              │               │
┌────────▼───┐  ┌───────▼──────┐  ┌────▼────────────┐
│ engine.py  │  │review_engine │  │review_dashboard │
│ Record     │  │ State file   │  │ Live polling    │
│ Transcribe │  │ Note writing │  │ Step UI         │
│ Refine     │  │ Narration    │  │ Streak label    │
└────────────┘  │ Streak       │  └─────────────────┘
                │ Focus trend  │
                │ Telegram     │
                └──────┬───────┘
         ┌─────────────┤
┌────────▼───┐  ┌──────▼──────────┐
│ telegram   │  │ morning_brief   │
│ _service   │  │ Reads priorities│
│ .py        │  │ Notifies + TTS  │
│ Pluggable  │  │ systemd timer   │
└────────────┘  └─────────────────┘
         │
┌────────▼───────────────────────────────────────────┐
│                   utils.py                          │
│   Config loading · Ollama calls · Lang detection    │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Install

```bash
git clone <repo-url>
cd voice_to_refinedtext
chmod +x install.sh
./install.sh
```

The installer handles system packages, Python venv, Ollama, AI models, and the global hotkey automatically.

### 2. Install desktop launchers (optional)

```bash
bash install_desktop.sh
```

Adds **AI Voice Refiner** and **Evening Review** to the GNOME app drawer. Run once after installation.

### 3. Piper TTS Setup (Recommended)

For natural-sounding voice narration in Evening Review:

```bash
# Install Piper
.venv/bin/pip install piper-tts

# Download model
mkdir -p models
wget -P models "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
wget -P models "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
```

Then switch **TTS Engine** to `piper` in **Settings → Evening Review**.

### 4. Telegram Notifications (Optional)

1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the **bot token**
2. Message [@userinfobot](https://t.me/userinfobot) → copy your **chat ID**
3. Open **Settings → Notifications** in the tray app, paste token + chat ID, click **Send Test Message**

Once configured, review completion and morning briefs are sent to your phone automatically.

### 5. Morning Priority Briefing (Optional)

```bash
bash install_morning_brief.sh
```

Installs a systemd user timer that runs `morning_brief.py` at the time set in **Settings → Notifications → Brief Time**. Reads yesterday's Tomorrow's Priorities and narrates them aloud + sends Telegram. Re-run after changing the time.

### 6. Start the tray

```bash
python3 tray_app.py
# or from the GNOME app drawer: search "Voice Refiner"
```

A dot appears in your system tray. Right-click for the full menu.

### 7. Record

- **X11**: Press `Ctrl+Alt+V` anywhere
- **Wayland**: Configure a GNOME Custom Shortcut (see [Wayland Setup](#wayland-setup))
- Or click **Start Recording** in the tray menu

Speak. Pause. The refined text appears in your clipboard.

### 8. Evening Review

Right-click tray → **Start Evening Review**. The dashboard opens and guides you through each step with voice narration.

---

## Wayland Setup

On Wayland, `xbindkeys` cannot intercept global hotkeys. Use a **GNOME Custom Shortcut** instead:

1. **Settings → Keyboard → View and Customise Shortcuts → Custom Shortcuts → +**
2. **Name**: Voice Refiner  
   **Command**: `pkill -USR1 -f tray_app.py`  
   **Shortcut**: `Ctrl+Alt+V`

This sends a Unix signal to the running tray, which toggles recording — exactly like the hotkey would.

---

## Configuration

All settings are editable via the **Settings** window (tray → Settings) or directly in the JSON files.

### `config.json` — Voice Refiner

```json
{
    "WHISPER_MODEL": "large-v3-turbo",
    "OLLAMA_HOST": "http://localhost:11434",
    "OLLAMA_MODELS": {
        "en": "qwen2.5:3b",
        "hi": "mashriram/sarvam-1:latest"
    },
    "MODE": "refine",
    "SAMPLE_RATE": 16000,
    "SILENCE_THRESHOLD": 300,
    "SILENCE_DURATION": 2.0,
    "TEMPERATURE": 0.1,
    "SAVE_TO_MARKDOWN": false,
    "MARKDOWN_PATH": "~/Documents/VoiceNotes",
    "DIRECT_TYPING": false
}
```

| Key | Description |
|---|---|
| `WHISPER_MODEL` | Whisper model size — `tiny`, `base`, `small`, `medium`, `large-v3-turbo` |
| `OLLAMA_MODELS.en` | Model for English refinement |
| `OLLAMA_MODELS.hi` | Model for Hindi refinement/translation |
| `MODE` | `refine` (clean up in same language) or `translate` (Hindi → English) |
| `SILENCE_THRESHOLD` | Microphone energy threshold for silence detection; lower = more sensitive |
| `SILENCE_DURATION` | Seconds of silence before auto-stop |
| `DIRECT_TYPING` | If `true`, types refined text at cursor instead of (or in addition to) clipboard |

### `review_config.json` — Evening Review

```json
{
    "vault_paths": {
        "daily_notes": "~/learning_vault/My Daily Notes",
        "wellness_notes": "~/learning_vault/My Daily Notes/Wellness"
    },
    "review_expiry_hours": 1,
    "voice_narration": true,
    "tts_engine": "piper",
    "piper_model": "~/voice_to_refinedtext/models/en_US-ryan-high.onnx",
    "piper_model_hi": "~/voice_to_refinedtext/models/hi_IN-priyamvada-medium.onnx",
    "last_n_days_context": 3,
    "per_step_context": true,
    "structure_model": "qwen2.5:3b",
    "context_brief_language": "en",
    "brief_model": "qwen2.5:3b",
    "show_streak": true,
    "focus_word_trend": true,
    "morning_briefing_enabled": false,
    "morning_briefing_time": "08:00",
    "telegram_enabled": false,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "review_steps": [ ... ]
}
```

| Key | Default | Description |
|---|---|---|
| `vault_paths.daily_notes` | `~/learning_vault/My Daily Notes` | Root folder for daily notes (year/month subfolders created automatically) |
| `vault_paths.wellness_notes` | `~/learning_vault/My Daily Notes/Wellness` | Root folder for Wellness step notes |
| `review_expiry_hours` | `1` | Hours before an in-progress session is considered stale |
| `voice_narration` | `true` | Enable/disable step narration |
| `tts_engine` | `"espeak"` | `"espeak"` (built-in) or `"piper"` (neural, natural; needs model file) |
| `piper_model` | `""` | Full path to the English piper `.onnx` model file |
| `piper_model_hi` | `""` | Full path to the Hindi piper `.onnx` model file |
| `last_n_days_context` | `3` | Days of past notes read at review start for the context brief; set `0` to disable |
| `per_step_context` | `false` | Show step-relevant history from past notes in the dashboard panel as each step starts |
| `structure_model` | `null` | Ollama model for per-step LLM structuring; `null` uses the English model |
| `context_brief_language` | `"en"` | Language for the context brief narration and dashboard panel (`"en"` or `"hi"`) |
| `brief_model` | `null` | Ollama model for the context brief; `null` uses the English model |
| `show_streak` | `true` | Show 🔥 streak counter in dashboard header and narrate milestone completions |
| `focus_word_trend` | `true` | Record each day's focus word; narrate weekly trend on Sundays |
| `morning_briefing_enabled` | `false` | Enable the systemd morning briefing timer |
| `morning_briefing_time` | `"08:00"` | Time the morning brief fires (HH:MM); re-run `install_morning_brief.sh` after changing |
| `telegram_enabled` | `false` | Send notifications to Telegram |
| `telegram_bot_token` | `""` | Bot token from @BotFather |
| `telegram_chat_id` | `""` | Your personal Telegram chat ID |
| `review_steps[].structure_prompt` | (varies) | LLM prompt per step; use `{raw_text}` as the placeholder |
| `review_steps[].section_fill` | `false` | `true` = fill existing `### Header` in the note; `false` = append under `## Evening Review` |
| `review_steps[].isolate_file` | `false` | `true` = write to wellness note instead of daily note |
| `review_steps[].refine` | `true` | `false` = save raw transcription without LLM processing |
| `review_steps[].skip_default` | `""` | Text written to the note when this step is skipped (e.g. Movement → `"only office"`) |

---

## Known Issues & What Was Fixed

| Issue | Status | Fix |
|---|---|---|
| Tray icon visible but menu not clickable on GNOME | ✅ Fixed | Requires `gir1.2-ayatanaappindicator3-0.1` + `gi` symlink into venv |
| Hindi transcribed in Urdu script instead of Devanagari | ✅ Fixed | `initial_prompt` passed to Whisper forces Devanagari |
| Whisper hallucinating / translating mid-sentence | ✅ Fixed | Language-locked prompts via `langdetect` |
| Global hotkey not working on Wayland | ✅ Fixed | GNOME Custom Shortcut → `pkill -USR1 -f tray_app.py` |
| Evening Review step narrated twice | ✅ Fixed | Removed duplicate `send_step_notification` call before recording |
| `espeak-ng` audio captured by microphone as speech | ✅ Fixed | `blocking=True` narration waits for speech to finish before mic opens |
| Dashboard permanently stuck on "Initialising…" | ✅ Fixed | Expired-session detection added to `_poll_state` |
| Processing lock left set when another process held it | ✅ Fixed | `acquired_lock` pattern — `finally` only clears lock we actually set |
| Multiple dashboard windows from repeated cancel+start | ✅ Fixed | `pkill -f review_dashboard.py` before launching new instance |
| Dashboard hidden behind other windows | ✅ Fixed | `root.lift()` + temporary `topmost` on launch (`focus_force()` removed — caused GNOME focus-steal kill on Wayland) |
| Crash if cancel fires while LLM structuring thread runs | ✅ Fixed | `review_config` captured as local copy at thread start |
| `_fill_section` matching `### Meeting Notes` when looking for `### Meeting` | ✅ Fixed | Exact regex match instead of substring `find()` |
| `cycle_mode` clobbering all config settings | ✅ Fixed | Re-reads config from disk before writing, only updates `MODE` key |
| Log flooded with "State file not found" every 500 ms | ✅ Fixed | Removed log from `_load_state`; `_review_done` flag stops polling after completion |
| Redo leaves previous text in note file silently | ✅ Fixed | Desktop notification warns user to remove old text manually |
| Wellness step got wrong note template | ✅ Fixed | Separate `_create_wellness_note()` function |
| Dashboard opens then immediately disappears | ✅ Fixed | `_poll_state()` was called synchronously before `mainloop()` — `CTkButton.configure()` crashed Tcl/Tk; fixed by scheduling via `root.after(200, ...)` |
| Context panel shows raw token numbers (151644, 8948…) | ✅ Fixed | `str(response)` was dumping the full Ollama JSON dict; now uses `response.get("response", "")` |
| TTS narrating Ollama JSON / long garbage text | ✅ Fixed | Same root cause as above; also removed narration for "no notes found" fallback message |
| Exit menu item does not close tray app | ✅ Fixed | `faster-whisper` background thread kept process alive; `os._exit(0)` added after `icon.stop()` |

---

## Evening Review — How It Works

```
Start Review (tray menu) ── date prompt (today or past date)
        │
        ▼
initialize_review() ──── creates /tmp/review_state.json
        │                starts context brief background thread
        ▼
Dashboard opens ──────── polls state every 500 ms
        │                shows "📅 Analysing last N days…"
        │
        ▼  (background thread)
_run_context_brief() ─── reads last N daily notes
        │                LLM synthesises insight + nudge
        │                narrates brief aloud (piper/espeak)
        │                updates dashboard context panel
        ▼
Step 1 prompt narrated ── "Step 1: Focus Word. Please speak now."
        │
[User records Ctrl+Alt+V]
        │
        ▼
engine.record() ──── Whisper transcription
        │
        ▼
raw text appended to accumulated_raw[] in state file
        │
[User clicks ▶ Next Step]
        │
        ▼
LLM structures with step's structure_prompt
        │
        ▼
write_step_to_note() ──── appends to ~/learning_vault/.../YYYY-MM-DD.md
        │                  (section_fill steps replace existing ### block)
        ▼
advance_step() ──────────── moves to next step, narrates prompt
        │                    (per_step_context: context panel updates)
        ▼  (repeat for each step)
        │
complete_review() ───────── update_streak() → write streak_current to state
        │                    delete state file
        │                    milestone narration (7/14/30/100 days)
        │                    send_telegram() in background thread
        │                    generates AI summary in background
        ▼
Dashboard shows ✅ complete  (streak label shows new 🔥 count)

─── Morning Brief (separate systemd timer) ───────────────────────
morning_brief.py ───────── reads yesterday's Tomorrow's Priorities
        │                   saves /tmp/morning_brief_state.json
        │                   desktop notification + Telegram
        │                   narrates priorities aloud
        ▼
Tray shows "Replay Morning Brief" while state is fresh
```

---

## File Reference

```
voice_to_refinedtext/
│
├── tray_app.py           Main entry point — system tray, menus, hotkey, state routing
├── engine.py             Recording, Whisper transcription, Ollama refinement, logging
├── review_engine.py      Evening Review state machine, note writing, narration, streak, focus trend
├── review_dashboard.py   Evening Review live dashboard (customtkinter)
├── config_gui.py         Settings GUI — three tabs (Voice Refiner, Evening Review, Notifications)
├── telegram_service.py   Pluggable Telegram notification module (drop-in, no project imports)
├── morning_brief.py      Morning priority briefing — reads yesterday's priorities, narrates + notifies
├── utils.py              Shared helpers: config loading, Ollama calls, lang detection
├── main_gui.py           Standalone interactive GUI (record → refine → view)
├── voice_to_ai_clipboard.py  Legacy single-shot script (hotkey without tray)
├── compare_models.py     Test multiple Ollama models on the same input
│
├── config.json           Voice Refiner settings (auto-created on first run)
├── review_config.json    Evening Review settings (auto-created on first run)
├── streak.json           Streak tracking state — current/best/last_date (auto-created)
├── focus_words.jsonl     Append-only focus word history for weekly trend (auto-created)
├── log.json              Transcription history with timestamps
├── review_debug.log      Evening Review detailed trace log
│
├── requirements.txt      Python dependencies
├── install.sh            One-click system installer for Ubuntu
├── install_desktop.sh    GNOME app drawer launcher installer (run once after install.sh)
├── install_morning_brief.sh  Installs systemd user timer for morning briefing
│
├── sounds/
│   ├── start.oga         Recording start chime
│   ├── end.oga           Recording end chime
│   └── complete.oga      Refinement complete chime
│
├── prompts/
│   ├── stops.json        Per-model stop tokens
│   └── {model}/{lang}.txt  Per-model, per-language prompt templates
│
├── templates/
│   ├── daily_note.md     Daily note template (supports {{date}}, {{prev_day}}, {{next_day}}, {{mod_date}})
│   └── wellness_note.md  Wellness note template
│
└── docs/
    ├── setup_guide.md        Full installation and configuration reference
    ├── setup_summary.md      Quick-start summary
    ├── progress_tracker.md   Feature completion status
    ├── idea.md               Original vision and architecture notes
    ├── plan.md               Implementation planning notes
    └── GEMINI.md             AI assistant session notes
```

---

## Documentation Index

| Document | What's in it |
|---|---|
| [`docs/setup_guide.md`](docs/setup_guide.md) | Full installation guide: system requirements, step-by-step setup on a new PC, `review_config.json` field reference, daily note template, Wayland hotkey, troubleshooting tables |
| [`docs/setup_summary.md`](docs/setup_summary.md) | Quick-start checklist — what the installer does and how to test it |
| [`docs/progress_tracker.md`](docs/progress_tracker.md) | Feature completion table across all development phases |
| [`docs/idea.md`](docs/idea.md) | Original project vision, architecture diagram, planned features |
| [`docs/plan.md`](docs/plan.md) | Implementation planning notes |

---

## System Requirements

| Requirement | Details |
|---|---|
| OS | Ubuntu 20.04+ (tested on 22.04 / 24.04) |
| RAM | 8 GB minimum, 16 GB recommended |
| Disk | ~5 GB for models |
| Microphone | Any USB or built-in mic |
| Python | 3.10+ |
| Key packages | `espeak-ng`, `pulseaudio-utils`, `xclip`, `python3-tk` (base for customtkinter) |
| Tray support | `gir1.2-ayatanaappindicator3-0.1` + `gi` symlink in venv |

Install all system dependencies in one command:

```bash
sudo apt install -y python3-pip python3-venv python3-tk xclip pulseaudio-utils \
    espeak-ng python3-gi gir1.2-ayatanaappindicator3-0.1
```

---

## Debugging

**Watch Evening Review activity live:**
```bash
tail -f review_debug.log
```

**Check if a review is currently active:**
```bash
cat /tmp/review_state.json
```

**Test espeak-ng narration:**
```bash
espeak-ng "Step 1: Focus Word. Please speak now."
```

**Test piper narration:**
```bash
echo "Step 1: Focus Word. Please speak now." | \
    ~/.local/bin/piper --model models/en_US-lessac-medium.onnx --output_file /tmp/test.wav
paplay /tmp/test.wav
```

**List installed Ollama models:**
```bash
ollama list
```

**Run the settings GUI directly:**
```bash
.venv/bin/python config_gui.py
```
