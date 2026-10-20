# AI Voice Refiner

A **local, privacy-first** voice-to-text assistant, currently designed for Ubuntu desktop. Speak in English or Hindi — the system transcribes with Whisper, refines with a local LLM via Ollama, and delivers polished text to your clipboard. Audio transcription and LLM refinement can run locally; optional integrations such as Telegram require network access.

Built on top of this core, the **Evening Review** feature turns daily voice recordings into structured Obsidian notes — running a guided, step-by-step reflection session every evening with full LLM structuring per step.

**Audio to Ideas** adds saved-recording and folder processing through a separate GUI and CLI. **Clean paragraph** is the default, with optional Concise summary and Ideas and actions modes, editable prompt templates and Hindi/English/mixed-language preservation. It uses configurable cached Whisper models and local Ollama while retaining timestamped transcripts. See the [user guide](docs/audio_to_idea/usage.md) for setup, recovery, prompts and configuration on another PC.

```bash
python3 -m audio_to_idea gui
python3 -m audio_to_idea doctor --discover --check-ollama
python3 -m audio_to_idea process --input /path/to/recordings --output-dir /path/to/outputs
```

The module's settings live in `audio_to_idea_config.json`; the committed `audio_to_idea_config.example.json` is portable. Existing recording and Evening Review settings remain separate. Optional launch entries appear in the tray and main window when module integration is enabled. See the [developer guide](docs/audio_to_idea/developer_guide.md) for architecture, prompt/output contracts, safe extension and test commands; [verification](docs/audio_to_idea/verification.md) records actual results and open model-quality checks.

---

## Features

### Core Voice Refiner
- **High-speed modular ASR** — pluggable speech-to-text engines:
  - `transcribe-cpp` (Vulkan/GPU acceleration on NVIDIA RTX 3060, CPU fallback): runs **Nemotron 3.5 Streaming (0.6B Q8_0 GGUF)** in **~138 ms** (~69x real-time), with built-in punctuation and capitalization. Also supports Whisper GGUF/bin (e.g. `Whisper-Hindi2Hinglish-Apex`) and Voxtral Realtime GGUF.
  - `faster-whisper` (CTranslate2): large-v3, turbo, and custom Whisper models.
  - `handy-cli`: headless external CLI fallback using the Handy binary.
- **Model Profiles & Instant Switching** — switch active models (`nemotron_fast`, `whisper_turbo`, `whisper_large_v3`, `hinglish_apex`) directly from the Settings GUI or with a single click in the System Tray menu.
- **Wayland & X11 Direct Typing** — types refined text at cursor using `ydotool` (Wayland), `wtype`, or `xdotool` (X11).
- **Offline speech-to-text** via local models without cloud APIs
- **Local LLM refinement** via Ollama — grammar cleanup, professional rewriting
- **Bilingual** — auto-detects English vs Hindi, applies language-specific models and prompts
- **Silence-based auto-stop** — no fixed timer; recording ends naturally when you pause
- **Auto-clipboard** — refined text lands in your clipboard instantly
- **Direct typing mode** — optionally simulates keyboard input to insert text at cursor
- **Refine / Translate toggle** — switch between refining in the same language or translating Hindi → English
- **Audio feedback** — distinct chimes for recording start, end, and completion
- **System tray** — persistent coloured-dot indicator (grey/red/blue/green) with right-click menu and live active ASR profile title

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
- **Focus word trend** — records each day's focus word to `focus_words.jsonl`; on Sundays narrates the most-repeated word from the past 7 entries ("इस हफ्ते आपका सबसे ज़्यादा ध्यान … पर रहा।"); dashboard shows a horizontal bar chart of the last 7 days' focus words
- **Carry-forward tasks** — at a configurable step, reads unchecked `- [ ]` tasks from the previous day's vault note and narrates them; interactive checkboxes in the dashboard let you mark tasks done (writes `- [x]` back to the vault in real time); opt-in via `carryforward_tasks: true`
- **Voice wake-word control** — say "stop" / "रुको" to halt narration, "again" / "फिर से" to replay, "आगे" / "aage" to advance to the next step, or "छोड़ो" / "chodo" to skip the current step; uses `faster-whisper tiny` (no extra models needed, supports Hindi + English); active throughout the entire review session (not just during TTS); opt-in via `voice_control: true` in Settings → Notifications (restart tray to take effect)
- **Evening review reminder** — a systemd user timer fires `evening_reminder.py` at a configured time; sends a desktop notification + Telegram message if no review has been completed that day and no review is currently in progress; opt-in via `evening_reminder_enabled: true`; time set in Settings → Notifications
- **Review time tracking** — automatically records how many seconds were spent on each step; shows live per-step elapsed time in the dashboard (`Speak now · ⏱ 55s`) and per-step durations on completion (`Done · 1m 30s`)
- **Audio quality gate** — immediately after recording, computes RMS energy of the WAV file; if the recording is below half the silence threshold, shows a notification and plays a TTS warning ("Recording seems too quiet, please try again.") and aborts before transcription; avoids wasting LLM time on silent clips
- **Narration hotkeys** — `Ctrl+Alt+S` stops the current narration; `Ctrl+Alt+R` replays the last narration; always registered, no-op outside review
- **Telegram mobile notifications** — sends review-complete summary (with streak) and morning brief to your phone via a Telegram bot; configured in Settings → Notifications; powered by self-contained `telegram_service.py`
- **Morning priority briefing** — a systemd user timer runs `morning_brief.py` at a configured time; reads yesterday's Tomorrow's Priorities, sends a desktop notification + Telegram message, and narrates the list aloud; tray shows **Replay Morning Brief** while the state is fresh
- **Pending task story** — morning brief scans the last N daily notes (`pending_task_lookback_days`, default 7) for unchecked `- [ ]` tasks that recur across days; narrates a story grouped by age — 🚨 critical (`pending_task_critical_threshold`, default ≥5 days), ⚠️ warning (`pending_task_warn_threshold`, default 3–4 days), 📌 recent, 🆕 new; narration is emoji-free for clean TTS; notification and Telegram include emoji labels; set `pending_task_lookback_days: 0` to disable
- **Customisable daily note template** — edit `templates/daily_note.md` with `{{date}}`, `{{prev_day}}`, `{{next_day}}`, `{{mod_date}}` tokens; no code changes needed
- **Skip defaults** — skipping a step with a configured default (e.g. Movement → `only office`) writes that default to the note automatically
- **Live dashboard** — customtkinter window showing all steps, context panel, status icons, progress bar, streak label, and control buttons; context panel has **⏹ Stop**, **🔁 Replay**, **↺ Regenerate** buttons and an **EN · HI** language toggle for the context brief
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

### 1. Choose the application

This repository currently contains two Python applications with different dependency sets:

- **AI Voice Refiner / Evening Review**: the existing tray app and its companion scripts (`tray_app.py`, `engine.py`, `review_dashboard.py`). Its dependencies are listed in `requirements.txt`; the Ubuntu installer is `install.sh`.
- **Audio to Ideas**: a newer, separate GUI/CLI package in `audio_to_idea/`, with metadata in `pyproject.toml` and its own [user guide](docs/audio_to_idea/usage.md).

Do not assume that installing one dependency set installs or validates the other.

### 2. Set up the existing Ubuntu tray app

The maintained setup path currently targets Ubuntu desktop. Review `install.sh` before running it: it uses `apt`, may install Ollama, downloads Ollama models, and configures an X11 hotkey. It is not a cross-platform installer and is not a minimal venv-repair command.

```bash
git clone <repo-url>
cd voice_to_refinedtext
./install.sh
```

The script creates a project-local `.venv` and installs `requirements.txt`. It also configures Ubuntu-specific tray and desktop integrations. On Wayland, follow the [Wayland Setup](#wayland-setup) instructions instead of relying on `xbindkeys`.

For a machine where the system Python is newer than the versions previously tested, do not assume the pinned requirements install unchanged. Use the Python version and dependency set documented as tested for the release. A venv is tied to its Python interpreter and operating system; recreate it on another machine rather than copying `.venv`. See [Environment support and troubleshooting](#environment-support-and-troubleshooting).

### 3. Install desktop launchers (optional)

```bash
bash install_desktop.sh
```

Adds **AI Voice Refiner** and **Evening Review** to the GNOME app drawer. Run once after installation.

### 4. Piper TTS Setup (Recommended)

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

### 5. Telegram Notifications (Optional)

1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the **bot token**
2. Message [@userinfobot](https://t.me/userinfobot) → copy your **chat ID**
3. Open **Settings → Notifications** in the tray app, paste token + chat ID, click **Send Test Message**

Once configured, review completion and morning briefs are sent to your phone automatically.

### 6. Morning Priority Briefing (Optional)

```bash
bash install_morning_brief.sh
```

Installs a systemd user timer that runs `morning_brief.py` at the time set in **Settings → Notifications → Brief Time**. Reads yesterday's Tomorrow's Priorities and narrates them aloud + sends Telegram. Re-run after changing the time.

### 7. Voice Wake-Word Control (Optional)

Enable hands-free narration control during Evening Review:

1. Open **Settings → Notifications → Voice Wake-Word Control**
2. Check **Enable Voice Control**, set threshold (default 500 is fine to start)
3. Click **Save** then **restart the tray**

While TTS is speaking:
- **"stop" / "रुको"** — halt narration
- **"again" / "फिर से"** — replay narration
- **"आगे" / "aage" / "अगला"** — advance to the next step
- **"छोड़ो" / "chodo"** — skip the current step

Alternatively use keyboard hotkeys at any time: `Ctrl+Alt+S` (stop) · `Ctrl+Alt+R` (replay).

### 8. Evening Review Reminder (Optional)

```bash
bash install_evening_reminder.sh
```

Installs a systemd user timer that fires at the time set in **Settings → Notifications → Evening Review Reminder**. If no review was completed that day, sends a desktop notification and (if configured) a Telegram message. Re-run after changing the reminder time.

### 9. Start the tray

```bash
.venv/bin/python tray_app.py
# or from the GNOME app drawer: search "Voice Refiner"
```

A dot appears in your system tray. Right-click for the full menu.

### 10. Record

- **X11**: Press `Ctrl+Alt+V` anywhere
- **Wayland**: Configure a GNOME Custom Shortcut (see [Wayland Setup](#wayland-setup))
- Or click **Start Recording** in the tray menu

Speak. Pause. The refined text appears in your clipboard.

### 11. Evening Review

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

> **📘 Detailed User Manual**: For hardware presets (RTX 3060 vs Low-VRAM Office PC), field-by-field reference tables, and tuning tips, see the [Comprehensive Configuration Guide](docs/CONFIGURATION_GUIDE.md).

All settings are editable via the **Settings** window (tray → Settings) or directly in the JSON files.

### `config.json` — Voice Refiner

```json
{
    "SAMPLE_RATE": 16000,
    "ASR_ENGINE": "transcribe_cpp",
    "ACTIVE_MODEL_PROFILE": "nemotron_fast",
    "WHISPER_MODEL": "large-v3-turbo",
    "MODEL_PROFILES": {
        "nemotron_fast": {
            "backend": "transcribe_cpp",
            "family": "nemotron",
            "path": "/media/manoj/F1/models-handy/nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf",
            "device": "auto"
        },
        "whisper_large_v3": {
            "backend": "faster_whisper",
            "family": "whisper",
            "path": "large-v3",
            "device": "auto"
        },
        "whisper_turbo": {
            "backend": "faster_whisper",
            "family": "whisper",
            "path": "large-v3-turbo",
            "device": "auto"
        },
        "hinglish_apex": {
            "backend": "transcribe_cpp",
            "family": "whisper",
            "path": "/media/manoj/F1/models-handy/Whisper-Hindi2Hinglish-Apex-Q8.bin",
            "device": "auto"
        }
    },
    "OLLAMA_HOST": "http://localhost:11434",
    "OLLAMA_MODELS": {
        "en": "qwen2.5:3b",
        "hi": "mashriram/sarvam-1:latest"
    },
    "MODE": "refine",
    "SILENCE_THRESHOLD": 300,
    "SILENCE_DURATION": 2.0,
    "TEMPERATURE": 0.1,
    "SAVE_TO_MARKDOWN": false,
    "MARKDOWN_PATH": "~/Documents/VoiceNotes",
    "DIRECT_TYPING": false,
    "FEATURES": {
        "start_end_sounds": true,
        "clipboard_output": true,
        "markdown_output": false,
        "direct_typing": false,
        "evening_review": true
    }
}
```

| Key | Description |
|---|---|
| `ASR_ENGINE` | Active ASR engine backend: `transcribe_cpp` (GGUF/Vulkan/CPU), `faster_whisper` (CTranslate2), or `handy_cli` |
| `ACTIVE_MODEL_PROFILE` | Name of active profile from `MODEL_PROFILES` (e.g. `nemotron_fast`, `whisper_turbo`) |
| `MODEL_PROFILES` | Dictionary of named model profiles mapping to model paths, families, and compute devices |
| `WHISPER_MODEL` | Fallback Whisper model size — `tiny`, `base`, `small`, `medium`, `large-v3-turbo` |
| `OLLAMA_MODELS.en` | Model for English refinement |
| `OLLAMA_MODELS.hi` | Model for Hindi refinement/translation |
| `MODE` | `refine` (clean up in same language) or `translate` (Hindi → English) |
| `SILENCE_THRESHOLD` | Microphone energy threshold for silence detection; lower = more sensitive |
| `SILENCE_DURATION` | Seconds of silence before auto-stop |
| `DIRECT_TYPING` | If `true`, types refined text at cursor via `ydotool` (Wayland), `wtype`, or `xdotool` (X11) |
| `FEATURES.start_end_sounds` | Play audio cues when recording starts and stops |
| `FEATURES.clipboard_output` | Copy refined text to clipboard after processing |
| `FEATURES.markdown_output` | Also save to Markdown file (requires `SAVE_TO_MARKDOWN` path) |
| `FEATURES.direct_typing` | Type refined text at cursor |
| `FEATURES.evening_review` | Show **Start Evening Review** in the tray menu |

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
| `brief_model` | `null` | Ollama model for the context brief (single-model mode); `null` uses the structure model |
| `brief_model_en` | `null` | English model for context brief (two-model mode); set both `brief_model_en` and `brief_model_hi` to enable parallel generation |
| `brief_model_hi` | `null` | Hindi model for context brief (two-model mode) |
| `show_streak` | `true` | Show 🔥 streak counter in dashboard header and narrate milestone completions |
| `focus_word_trend` | `true` | Record each day's focus word; narrate weekly trend on Sundays |
| `carryforward_tasks` | `false` | At the carry-forward step, read unchecked tasks from yesterday's note and show them as interactive checkboxes |
| `carryforward_step_id` | `3` | Step number (1-based) at which carry-forward tasks are narrated and shown |
| `morning_briefing_enabled` | `false` | Enable the systemd morning briefing timer |
| `morning_briefing_time` | `"08:00"` | Time the morning brief fires (HH:MM); re-run `install_morning_brief.sh` after changing |
| `pending_task_lookback_days` | `7` | How many past daily notes the morning brief scans for recurring unchecked tasks; set `0` to disable the pending story entirely |
| `pending_task_warn_threshold` | `3` | Days a task has been pending before it gets the ⚠️ warning label in the story |
| `pending_task_critical_threshold` | `5` | Days a task has been pending before it gets the 🚨 critical label in the story |
| `voice_control` | `false` | Opt-in: listen for spoken commands during narration (`stop`/`रुको`, `again`/`फिर से`, `आगे`/`aage` for next step, `छोड़ो`/`chodo` to skip) |
| `voice_control_threshold` | `500` | RMS energy gate (0–32768 int16 scale); raise if TTS speaker bleed triggers false positives |
| `evening_reminder_enabled` | `false` | Send a reminder if the review is not done by the reminder time |
| `evening_reminder_time` | `"21:00"` | Time the reminder fires (HH:MM); re-run `install_evening_reminder.sh` after changing |
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
| Redo leaves previous text in note file | ✅ Fixed | `write_step_to_note` records byte offset; `redo_step` truncates file at that position — fully automatic for append steps; section_fill steps still warn manually |
| Wellness step got wrong note template | ✅ Fixed | Separate `_create_wellness_note()` function |
| Dashboard opens then immediately disappears | ✅ Fixed | `_poll_state()` was called synchronously before `mainloop()` — `CTkButton.configure()` crashed Tcl/Tk; fixed by scheduling via `root.after(200, ...)` |
| Context panel shows raw token numbers (151644, 8948…) | ✅ Fixed | `str(response)` was dumping the full Ollama JSON dict; now uses `response.get("response", "")` |
| TTS narrating Ollama JSON / long garbage text | ✅ Fixed | Same root cause as above; also removed narration for "no notes found" fallback message |
| Exit menu item does not close tray app | ✅ Fixed | `faster-whisper` background thread kept process alive; `os._exit(0)` added after `icon.stop()` |
| `FEATURES.clipboard_output` / `direct_typing` toggles had no effect | ✅ Fixed | `_run_normal_mode` was reading the old flat `DIRECT_TYPING` key and running `xclip` unconditionally; now reads `FEATURES` block |
| TOCTOU race: two simultaneous "Next Step" clicks could run the LLM twice | ✅ Fixed | `structure_and_advance` now acquires an exclusive file lock (`/tmp/review_processing.lock`) with `LOCK_NB` before any state check — concurrent caller bails immediately |
| `self.is_processing` flag in tray/dashboard could diverge from `state["processing"]` | ✅ Fixed | Both in-memory flags removed; `state["processing"]` in the state file is the sole guard for all processes |
| Tray menu stuck showing review items after dashboard-driven completion | ✅ Fixed | `_watch_review_completion` daemon thread polls `is_review_active()` every 2 s; calls `_review_finished()` as soon as state disappears |

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
├── review_engine.py      Evening Review state machine, note writing, narration, streak, focus trend; public API for all external callers (tray, dashboard, morning_brief, evening_reminder)
├── review_dashboard.py   Evening Review live dashboard (customtkinter)
├── config_gui.py         Settings GUI — four tabs (Voice Refiner, Evening Review, Notifications, Features)
├── theme.py              Shared UI colour palette (Catppuccin Mocha) — imported by all GUI files
├── telegram_service.py   Pluggable Telegram notification module (drop-in, no project imports)
├── morning_brief.py      Morning priority briefing — reads yesterday's priorities, narrates + notifies
├── voice_control.py      Wake-word listener — detects stop/replay commands during TTS narration
├── utils.py              Shared helpers: config loading, Ollama calls, lang detection, logging setup
├── main_gui.py           Standalone interactive GUI (record → refine → view)
├── voice_to_ai_clipboard.py  Legacy single-shot script (hotkey without tray)
├── compare_models.py     Test multiple Ollama models on the same input
├── calibrate_threshold.py  Guided mic calibration utility — measures speech vs silence RMS and recommends SILENCE_THRESHOLD
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
├── evening_reminder.py       Evening reminder — fires if no review done; notifies desktop + Telegram
├── install_evening_reminder.sh  Installs systemd user timer for evening reminder
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
    ├── idea.md               Original vision and architecture notes
    ├── GEMINI.md             AI assistant session notes
    ├── refactor/
    │   ├── plan.md           Active refactoring plan (modularisation, bug fixes, configurability)
    │   ├── steps.md          Granular implementation checklist
    │   └── progress.md       Refactoring progress tracker
    └── archive/
        ├── plan_phases1to5.md        Original development plan (Phases 1–5, all completed)
        └── progress_phases1to5.md    Original progress tracker (all ✅)
```

---

## Documentation Index

| Document | What's in it |
|---|---|
| [`docs/setup_guide.md`](docs/setup_guide.md) | Full installation guide: system requirements, step-by-step setup on a new PC, `review_config.json` field reference, daily note template, Wayland hotkey, troubleshooting tables |
| [`docs/setup_summary.md`](docs/setup_summary.md) | Quick-start checklist — what the installer does and how to test it |
| [`docs/refactor/plan.md`](docs/refactor/plan.md) | Active refactoring plan — architecture decisions, phases, what changed and why |
| [`docs/refactor/progress.md`](docs/refactor/progress.md) | Refactoring task progress tracker |
| [`docs/audio_to_idea/plan.md`](docs/audio_to_idea/plan.md) | AudioToIdea integration architecture, portable configuration, model compatibility, and phased delivery plan |
| [`docs/audio_to_idea/implementation_steps.md`](docs/audio_to_idea/implementation_steps.md) | Ordered AudioToIdea implementation tasks and verification gates |
| [`docs/audio_to_idea/progress_tracker.md`](docs/audio_to_idea/progress_tracker.md) | AudioToIdea progress, release checklist, findings, and evidence log |
| [`docs/audio_to_idea/test_matrix.md`](docs/audio_to_idea/test_matrix.md) | AudioToIdea acceptance checks and existing-app regression requirements |
| [`docs/audio_to_idea/usage.md`](docs/audio_to_idea/usage.md) | AudioToIdea GUI/CLI user guide, portable model configuration, output recovery, and troubleshooting |
| [`docs/audio_to_idea/developer_guide.md`](docs/audio_to_idea/developer_guide.md) | Implemented architecture, processing/template/cache contracts, theme maintenance, legacy isolation, tests and packaging |
| [`docs/audio_to_idea/verification.md`](docs/audio_to_idea/verification.md) | Executed tests, model/CPU packaging evidence, preservation checks, and remaining manual qualification |
| [`docs/idea.md`](docs/idea.md) | Original project vision, architecture diagram, planned features |

---

## System Requirements

| Requirement | Details |
|---|---|
| OS | Ubuntu desktop is the current target. Historical testing is documented for 22.04 / 24.04; 26.04 was manually brought up using a local venv. Other distributions and operating systems are not yet qualified. |
| RAM | 8 GB minimum, 16 GB recommended |
| Disk | ~5 GB for models |
| Microphone | Any USB or built-in mic |
| Python | Use a version verified for the chosen app and dependency set. `pyproject.toml` applies to Audio to Ideas; `requirements.txt` applies to the tray app. The repository does not yet have a complete cross-version CI support matrix. |
| Key packages | `espeak-ng`, `pulseaudio-utils`, `xclip`, `python3-tk` (base for customtkinter) |
| Tray support | Ubuntu/GNOME integration currently uses system GObject introspection (`python3-gi`) and Ayatana AppIndicator; setup is distribution-specific. |

On Ubuntu, these are the system packages expected by the current tray-app setup (the `install.sh` script installs them). Package names and desktop integrations differ on other systems:

```bash
sudo apt install -y python3-pip python3-venv python3-tk xclip pulseaudio-utils \
    espeak-ng python3-gi gir1.2-ayatanaappindicator3-0.1
```

---

## Environment support and troubleshooting

The project does not yet claim support for every operating system or Python version. The existing tray app depends on native audio, clipboard, tray, and hotkey integrations; those parts are operating-system and desktop-session specific. Ubuntu is the current target. Windows, macOS, and non-Ubuntu Linux distributions need separate setup instructions and testing before they can be called supported.

There are two independent Python dependency definitions today: `requirements.txt` for the tray app and `pyproject.toml` for Audio to Ideas. Their dependency lists are not interchangeable. In particular, older exact pins in `requirements.txt` may not install on newer Python releases. Prefer a clean venv using a Python version and dependency set verified for the app; do not copy a venv between machines or operating systems.

On Ubuntu 26.04, the tray app was made to run in a local `.venv` with Python 3.14 and newer compatible packages, while exposing Ubuntu's system Python modules through `--system-site-packages`. This is a machine-specific recovery, not yet a reproducible, tested installation recipe for all systems. A future release should consolidate dependency declarations, define supported Python versions, and verify them in CI before advertising broader compatibility.

`install.sh` is an Ubuntu convenience script with side effects: it uses `apt`, may install Ollama, pulls models, links system `gi` into the venv, and configures an X11 hotkey. Review it before running. It is not a generic installer or a safe way to repair only an existing venv.

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

**Calibrate your microphone silence threshold:**
```bash
python3 calibrate_threshold.py
```

Guides you through 3 rounds of speak → silence, measures RMS energy levels, and recommends the best `SILENCE_THRESHOLD` value for your mic and environment. Has a one-click **Apply to config.json** button.
