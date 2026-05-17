# Voice-to-Refined Text AI Assistant — Setup Guide

This guide covers setting up the fully local, offline-capable voice-to-text AI assistant on Ubuntu, including the **Evening Review** feature that records structured daily notes into an Obsidian vault.

---

## 1. System Requirements

### Operating System
- Ubuntu 20.04 or newer (tested on 22.04 / 24.04)

### Hardware
- Microphone for audio input
- 8 GB+ RAM (16 GB recommended for large Whisper models)
- ~5 GB disk space for AI models

### System Packages

| Package | Purpose |
|---|---|
| `python3`, `python3-pip`, `python3-venv` | Python runtime |
| `python3-tk` | Base tkinter required by customtkinter |
| `xclip` | Clipboard management |
| `pulseaudio-utils` | `paplay` sound feedback (start/end chimes) |
| `espeak-ng` | **Voice narration** for Evening Review step prompts |
| `ollama` | Local LLM inference |
| `python3-gi`, `gir1.2-ayatanaappindicator3-0.1` | Clickable tray icons on Ubuntu/GNOME |

> **Note for Wayland users**: `xbindkeys` is NOT used for Wayland. See [Section 5.3](#53-wayland-hotkey-gnome-only) for the GNOME custom shortcut approach.

---

## 2. Installation (Automatic)

```bash
cd voice_to_refinedtext
chmod +x install.sh
./install.sh
```

The installer handles system packages, Python virtual environment, Ollama models, and hotkey configuration.

> **What `install.sh` does:**
> - Installs all system packages (including `espeak-ng`)
> - Installs and starts Ollama, pulls required models
> - Creates `.venv` and installs Python dependencies
> - Symlinks the system `gi` library into the venv (required for pystray on GNOME)
> - Configures the `Ctrl+Alt+V` hotkey via `xbindkeys`

---

## 3. New PC Deployment — Step by Step

### 3.1. Copy the Project

```bash
git clone <repo-url>   # or copy the folder
cd voice_to_refinedtext
```

### 3.2. Run the Installer

```bash
chmod +x install.sh
./install.sh
```

Provide your `sudo` password when prompted. The script exits on the first error (`set -e`), so fix any reported issue and re-run.

### 3.3. Verify Ollama

```bash
ollama list          # should show qwen2.5:3b and sarvam-1
ollama run qwen2.5:3b "Hello"   # quick smoke test
```

### 3.4. Start the Tray

```bash
.venv/bin/python tray_app.py
```

A coloured dot appears in the system tray. Right-click for the menu.

### 3.5. Auto-Start on Boot (Optional)

Open **Startup Applications** → **Add**:

- **Name**: AI Voice Refiner
- **Command**: `/absolute/path/to/project/.venv/bin/python /absolute/path/to/project/tray_app.py`

---

## 4. Evening Review — Additional Requirements

The Evening Review feature records structured daily reflections and writes them into an Obsidian-compatible Markdown vault.

### 4.1. Voice Narration (TTS)

The system speaks each step prompt aloud when a review step begins. Two engines are supported:

#### Option A — espeak-ng (default, no setup needed)

```bash
sudo apt install espeak-ng
espeak-ng "Hello, Evening Review is ready."   # verify it works
```

espeak-ng is the fallback engine. It works immediately after install with no model files required.

#### Option B — Piper (neural voice, much more natural)

Piper is a local neural TTS engine that produces high-quality speech with no cloud dependency.

**1. Install piper:**

```bash
.venv/bin/pip install piper-tts
```

Piper installs to `~/.local/bin/piper`. It is found automatically — no PATH changes needed.

**2. Download a voice model:**

Models live in the project `models/` directory. Download both files (the `.onnx` model and its `.onnx.json` config):

```bash
mkdir -p models
cd models
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
```

The lessac-medium model is ~61 MB and sounds natural for narration.

**3. Switch to piper in Settings:**

Open **Settings → Evening Review → Text-to-Speech**:
- Set **TTS Engine** to `piper`
- Set **Piper Model Path** to the full path of the `.onnx` file, e.g.:
  `/home/you/voice_to_refinedtext/models/en_US-lessac-medium.onnx`

Or edit `review_config.json` directly:

```json
{
    "tts_engine": "piper",
    "piper_model": "/home/you/voice_to_refinedtext/models/en_US-lessac-medium.onnx"
}
```

**Test piper directly:**

```bash
echo "Step one: speak your focus word." | ~/.local/bin/piper \
    --model models/en_US-lessac-medium.onnx --output_file /tmp/test.wav
paplay /tmp/test.wav
```

> **Fallback**: if piper is not found or the model file is missing, the system automatically falls back to espeak-ng so narration never silently breaks.

**Disabling narration entirely:**

Set `"voice_narration": false` in `review_config.json`, or uncheck **Voice Narration** in Settings.

### 4.2. Obsidian Vault Structure

The system writes notes to this folder structure:

```
~/learning_vault/
  My Daily Notes/
    2025/
      May/
        2025-05-16.md      ← daily note (Evening Review appended here)
    My Daily Notes/Wellness/
      2025/
        May/
          2025-05-16.md    ← wellness-only entries
```

**The system creates these folders automatically** when a review starts. You do not need to create them manually.

> If your Obsidian vault is at a different path, update it in **Settings → Evening Review → Vault Paths** before the first review, or edit `review_config.json` directly.

### 4.3. `review_config.json` Reference

This file is created in the project directory after the first run (or you can create it manually). All fields are optional — missing values use the defaults shown.

```json
{
    "vault_paths": {
        "base_vault": "~/learning_vault",
        "daily_notes": "~/learning_vault/My Daily Notes",
        "wellness_notes": "~/learning_vault/My Daily Notes/Wellness"
    },
    "review_expiry_hours": 1,
    "voice_narration": true,
    "tts_engine": "piper",
    "piper_model": "~/voice_to_refinedtext/models/en_US-lessac-medium.onnx",
    "last_n_days_context": 3,
    "per_step_context": false,
    "structure_model": null,
    "review_steps": [
        {
            "step_id": 1,
            "section_name": "Focus Word",
            "prompt_notification": "Step 1/6: Speak today's core focus word.",
            "section_fill": false,
            "isolate_file": false,
            "skippable": true,
            "refine": true,
            "structure_prompt": "Extract the single core focus word from this voice note. Output only the word:\n{raw_text}"
        }
    ]
}
```

| Key | Default | Description |
|---|---|---|
| `vault_paths.daily_notes` | `~/learning_vault/My Daily Notes` | Root folder for daily notes |
| `vault_paths.wellness_notes` | `~/learning_vault/My Daily Notes/Wellness` | Root folder for wellness notes |
| `review_expiry_hours` | `1` | Hours before an unfinished review session is considered stale |
| `voice_narration` | `true` | Whether step prompts are narrated aloud |
| `tts_engine` | `"espeak"` | TTS engine: `"espeak"` (built-in, no setup) or `"piper"` (neural, natural-sounding) |
| `piper_model` | `""` | Full path to the piper `.onnx` model file (only used when `tts_engine` is `"piper"`) |
| `last_n_days_context` | `3` | Days of past notes read at review start for the AI context brief; set `0` to disable |
| `per_step_context` | `false` | Show step-relevant history from past notes in the context panel as each step starts |
| `structure_model` | `null` | Ollama model for LLM structuring; `null` uses the English model from `config.json` |
| `review_steps[].section_fill` | `false` | If `true`, fills an existing `### SectionName` block in the note rather than appending under `## Evening Review` |
| `review_steps[].isolate_file` | `false` | If `true`, writes to the wellness note instead of the daily note |
| `review_steps[].refine` | `true` | If `false`, raw transcription is saved without LLM structuring |
| `review_steps[].structure_prompt` | (varies) | LLM prompt template; use `{raw_text}` as the placeholder for the transcription |
| `review_steps[].skip_default` | `""` | Text written to the note when this step is skipped (e.g. Movement → `"only office"`) |

### 4.4. Last-N-Days Context Brief

When a review starts, the system reads the last N daily notes (default: 3), extracts their `## Evening Review` sections, and asks the local LLM to synthesise a brief insight. This brief is:

- **Narrated aloud** (via piper/espeak) before Step 1 begins
- **Displayed** in the `📅 Context` panel at the top of the dashboard

The dashboard shows "Analysing last N days…" while the LLM runs in the background. Once ready, the brief appears and the Step 1 prompt is narrated.

**If no past notes exist:**
> "No evening review notes found for the last 3 days."

**Configuring:**

| Setting | Default | Effect |
|---|---|---|
| `last_n_days_context` | `3` | Number of past days to read; set `0` to skip context entirely |
| `per_step_context` | `false` | When `true`, the context panel updates per step to show that step's history from past notes |

Both are available in **Settings → Evening Review → Review Behaviour**.

### 4.5. Daily Note Template

When the system creates a new daily note (because Obsidian hasn't created it yet), it reads from `templates/daily_note.md` in the project directory. You can edit this file freely — no code changes needed.

**Supported tokens:**

| Token | Replaced with |
|---|---|
| `{{date}}` | Note date (e.g. `2026-05-16`) |
| `{{prev_day}}` | Previous day ISO date |
| `{{next_day}}` | Next day ISO date |
| `{{mod_date}}` | Current datetime (e.g. `Saturday 16th May 2026 21:30:00`) |

**Default template (`templates/daily_note.md`):**

```markdown
---
creation date: {{date}}
modification date: {{mod_date}}
---

<< [[{{prev_day}}]] | [[{{next_day}}]] >>

# {{date}}

### Meeting

### Movement

## Evening Review
```

> If `templates/daily_note.md` is missing, the system falls back to a hardcoded template and logs a warning.

Evening Review sections are appended below `## Evening Review`. Steps configured with `section_fill: true` (Meeting, Movement) fill their matching `### Header` blocks.

---

## 5. Usage

### 5.1. Tray Icon Colours

| Colour | State |
|---|---|
| Grey | Idle |
| Red | Recording |
| Blue | Processing (transcribing / LLM running) |
| Green | Evening Review in progress |

### 5.2. Starting an Evening Review

1. Right-click the tray icon → **Start Evening Review**
2. A date prompt appears — press OK for today, or type a past date (`YYYY-MM-DD`) for a back-fill review
3. The **Evening Review Dashboard** opens; the `📅 Context` panel shows "Analysing last N days…"
4. The system reads the last N daily notes, generates an AI brief, and narrates it aloud
5. Step 1 is then narrated: *"Step 1: Focus Word. Please speak now."*
6. Press the **Record** button (or use `Ctrl+Alt+V` / the GNOME shortcut) and speak
7. Recording stops automatically on silence
8. Click **▶ Next Step** to run LLM structuring and advance
9. Repeat for each step; click **⏭ Skip** to skip (steps with a `skip_default` write it automatically)
10. When all steps complete, the daily note is updated and an AI summary is appended

### 5.3. Wayland Hotkey (GNOME Only)

On Wayland, `xbindkeys` does not work for global hotkeys. Use a **GNOME Custom Shortcut** instead:

1. Open **Settings → Keyboard → View and Customise Shortcuts → Custom Shortcuts**
2. Click **+** and add:
   - **Name**: Voice Refiner Record
   - **Command**: `pkill -USR1 -f tray_app.py`
   - **Shortcut**: `Ctrl+Alt+V`

This sends a `SIGUSR1` signal to the running tray, which toggles recording exactly like the hotkey would.

### 5.4. Dashboard Controls

| Button | Action |
|---|---|
| 🎤 Record | Toggle recording for the current step (same as hotkey) |
| ▶ Next Step | Run LLM structuring on recorded clips and advance to next step |
| ⏭ Skip | Skip the current step without recording |
| ↩ Redo | Clear recorded clips and re-prompt (note: previous text in the file must be removed manually) |
| ✕ Cancel Review | Cancel the review; progress so far is preserved in the note |

---

## 6. Configuration GUI

Launch the settings window from the tray → **Settings**, or directly:

```bash
.venv/bin/python config_gui.py
```

- **Tab 1 — Voice Refiner**: Whisper model, Ollama host, language models, silence detection
- **Tab 2 — Evening Review**: Vault paths, narration toggle, expiry hours, structuring model, per-step prompts

---

## 7. Logs and Debugging

| File | Contents |
|---|---|
| `log.json` | All voice transcriptions and refinements with timestamps |
| `review_debug.log` | Detailed trace of every Evening Review action (state saves, LLM calls, file writes, errors) |
| `/tmp/review_state.json` | Live review session state (deleted when review completes) |

To watch Evening Review activity in real time:
```bash
tail -f /path/to/project/review_debug.log
```

---

## 8. Common Issues

### Voice Refiner

| Symptom | Fix |
|---|---|
| Tray icon not clickable | Install `gir1.2-ayatanaappindicator3-0.1` and ensure the `gi` symlink exists in `.venv` |
| No clipboard output | Install `xclip` (`sudo apt install xclip`) |
| Ollama timeout | Use a smaller model (e.g. `qwen2.5:3b` instead of a 7B model) |
| No speech detected | Check microphone with `arecord -l`; adjust `SILENCE_THRESHOLD` in Settings |

### Evening Review

| Symptom | Fix |
|---|---|
| Dashboard doesn't appear | Restart the tray — it kills any stale dashboard windows before opening a new one |
| Dashboard opens behind other windows | It auto-raises for 2 seconds on launch; if still hidden, check your window manager's focus rules |
| "Initialising…" stuck after 1 hour | Review session expired; cancel via tray menu and start a new review |
| No voice narration | Install `espeak-ng` (`sudo apt install espeak-ng`); or disable narration in Settings |
| Note not created in vault | Check vault path in Settings → Evening Review matches your actual Obsidian vault location |
| Redo leaves duplicate text in note | By design — redo only clears the recording buffer; remove the previous text from the note file manually |
| `pkill -USR1` not working on Wayland | Ensure the tray is running and use the exact command `pkill -USR1 -f tray_app.py` |
| Review debug log shows `is_review_active → False (expired)` | `review_expiry_hours` is too short for your review pace; increase it in Settings |

---

## 9. File Reference

```
voice_to_refinedtext/
├── tray_app.py          # System tray app — main entry point
├── engine.py            # Recording, Whisper transcription, Ollama refinement
├── review_engine.py     # Evening Review state machine and note writing
├── review_dashboard.py  # Evening Review GUI dashboard
├── config_gui.py        # Settings window (both tabs)
├── utils.py             # Shared helpers (config loading, Ollama calls)
├── config.json          # Voice Refiner settings (auto-created)
├── review_config.json   # Evening Review settings (auto-created)
├── review_debug.log     # Evening Review debug log
├── log.json             # Voice transcription history
├── requirements.txt     # Python dependencies
├── install.sh           # One-click installer
├── sounds/
│   ├── start.oga        # Recording start chime
│   ├── end.oga          # Recording end chime
│   └── complete.oga     # Refinement complete chime
└── prompts/
    ├── stops.json        # Per-model stop tokens
    └── {model}/{lang}.txt  # Per-model, per-language prompt templates
```
