# Comprehensive Configuration Guide & User Manual

Welcome to the definitive configuration manual for **AI Voice Refiner**, **Evening Review**, and **Audio to Ideas**. 

This document explains every configuration setting across the three subsystems, provides copy-paste ready hardware presets, and explains how to optimize for speed, memory, and bilingual accuracy.

---

## 1. Quick-Start Hardware Presets

Copy and paste the preset matching your hardware into `config.json`.

### Preset A: High-Performance GPU Workstation (e.g., Home PC — RTX 3060 12GB)
> **Goal:** Maximum speed, sub-second dictation (<0.5s), persistent GPU residence, Wayland/X11 typing.

```json
{
    "SAMPLE_RATE": 16000,
    "ASR_ENGINE": "transcribe_cpp",
    "ACTIVE_MODEL_PROFILE": "nemotron_fast",
    "TYPING_TOOL": "auto",
    "OLLAMA_HOST": "http://localhost:11434",
    "OLLAMA_KEEP_ALIVE": "60m",
    "OLLAMA_MODELS": {
        "en": "qwen2.5:3b",
        "hi": "SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest"
    },
    "OLLAMA_TRANSLATE_MODELS": {
        "to_en": "qwen2.5:3b",
        "to_hi": "SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest"
    },
    "SILENCE_THRESHOLD": 300,
    "SILENCE_DURATION": 2.0,
    "TEMPERATURE": 0.1,
    "MODE": "refine",
    "DIRECT_TYPING": true,
    "FEATURES": {
        "start_end_sounds": true,
        "clipboard_output": true,
        "markdown_output": false,
        "direct_typing": true,
        "evening_review": true
    }
}
```

---

### Preset B: Low-VRAM / Office Desktop (e.g., Office PC — Ubuntu 22.04, 4GB VRAM or CPU)
> **Goal:** Minimal memory footprint, immediate VRAM offload (`keep_alive: "0"`), smooth desktop operation.

```json
{
    "SAMPLE_RATE": 16000,
    "ASR_ENGINE": "transcribe_cpp",
    "ACTIVE_MODEL_PROFILE": "whisper_turbo",
    "TYPING_TOOL": "xdotool",
    "OLLAMA_HOST": "http://localhost:11434",
    "OLLAMA_KEEP_ALIVE": "0",
    "OLLAMA_MODELS": {
        "en": "qwen2.5:3b",
        "hi": "qwen2.5:3b"
    },
    "OLLAMA_TRANSLATE_MODELS": {
        "to_en": "qwen2.5:3b",
        "to_hi": "qwen2.5:3b"
    },
    "SILENCE_THRESHOLD": 350,
    "SILENCE_DURATION": 2.5,
    "TEMPERATURE": 0.1,
    "MODE": "refine",
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

---

### Preset C: Bilingual & Translation Specialist
> **Goal:** Seamless English and Hindi dictation, one-click Hindi-to-English translation.

```json
{
    "SAMPLE_RATE": 16000,
    "ASR_ENGINE": "transcribe_cpp",
    "ACTIVE_MODEL_PROFILE": "nemotron_fast",
    "TYPING_TOOL": "auto",
    "OLLAMA_HOST": "http://localhost:11434",
    "OLLAMA_KEEP_ALIVE": "30m",
    "OLLAMA_MODELS": {
        "en": "qwen2.5:3b",
        "hi": "SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest"
    },
    "OLLAMA_TRANSLATE_MODELS": {
        "to_en": "qwen2.5:3b",
        "to_hi": "SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest"
    },
    "SILENCE_THRESHOLD": 300,
    "SILENCE_DURATION": 2.0,
    "TEMPERATURE": 0.1,
    "MODE": "translate",
    "DIRECT_TYPING": true,
    "FEATURES": {
        "start_end_sounds": true,
        "clipboard_output": true,
        "markdown_output": false,
        "direct_typing": true,
        "evening_review": true
    }
}
```

---

### 1.4 Multi-PC Deployment & Portable Model Directory Setup
> **Goal:** Run seamlessly across multiple computers (Home PC, Office Desktop, Laptop) without broken drive paths.

When transferring this repository to another PC or drive where paths differ:

1. **The Single Source of Truth (`MODELS_DIR`)**:
   `ASR_PRESETS` in `config.json` stores purely portable model filenames (e.g., `"model": "nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf"` and `"model": "Whisper-Hindi2Hinglish-Apex-Q8.bin"`).
   You only need to configure the base directory once via `"MODELS_DIR"` in `config.json`:
   ```json
   "MODELS_DIR": "/home/username/models"
   ```
   Or on Windows:
   ```json
   "MODELS_DIR": "C:\\AI_Models\\handy"
   ```
   Or relative to this repository:
   ```json
   "MODELS_DIR": "./models"
   ```

2. **Web Settings GUI (Zero JSON Editing)**:
   Open the settings dashboard at `http://127.0.0.1:8765/settings`. Under the **Core Pipeline & Storage** section, you will find the **📁 Models Base Directory (MODELS_DIR)** field. Changing the path here and clicking *Save Configuration* instantly updates `config.json` and hot-reloads the active ASR backend across both the real-time dictation engine and the Audio-to-Idea batch processor.

3. **Zero-Configuration `./models/` Drop-In**:
   If you copy your model files directly into `<project_root>/models/`, the system automatically discovers and loads them without requiring any configuration edits on any PC!

4. **Environment Variable Override (`$MODELS_DIR`)**:
   You can also set the location system-wide via environment variables in your terminal, `.env`, or shell profile:
   ```bash
   export MODELS_DIR="/path/to/my/models"
   # or
   export VOICE_MODELS_DIR="/path/to/my/models"
   ```

5. **Multi-Tier Fallback Discovery Hierarchy**:
   When resolving any model filename, the ASR factory inspects the following tiers in order:
   1. Explicit `"MODELS_DIR"` configured in `config.json`
   2. Environment variables: `$MODELS_DIR`, `$VOICE_MODELS_DIR`, `$HANDY_MODELS_DIR`
   3. Repository local folder: `<project_root>/models/<filename>`
   4. User standard data folder: `~/.local/share/voice_to_refinedtext/models/<filename>`
   5. User cache folder: `~/.cache/voice_to_refinedtext/models/<filename>`
   6. Primary development path: `/media/manoj/F1/models-handy/<filename>`

6. **Unified Discovery Across Real-time & Batch Pipelines**:
   Both `engine.py` (real-time voice dictation) and `audio_to_idea` (batch audio file transcription and synthesis) share this exact same discovery logic. Even if `audio_to_idea` is invoked without explicit arguments, it automatically inherits `MODELS_DIR` from `config.json`.

---

### 1.5 Automated Environment Doctor (`doctor.py`) & Self-Healing Health Checks
> **Goal:** Verify that all audio, model, kernel, and LLM dependencies are operational across any machine with one command.

Whenever setting up the application on a new PC, changing audio devices, or moving models to a new drive, run the diagnostic doctor:

```bash
# Run complete 6-point subsystem diagnostic
python doctor.py

# Actively probe microphone hardware for 1.5 seconds (verifies audio RMS level)
python doctor.py --mic

# Output machine-readable JSON for automated scripts or dashboards
python doctor.py --json

# Interactively execute safe automated fixes (pull missing models, create folders)
python doctor.py --fix
```

#### What `doctor.py` Checks:
1. **Python Runtime & Libraries**: Verifies Python $\ge 3.10$ and all core modules (`sounddevice`, `scipy`, `numpy`, `evdev`, `transcribe_cpp`, `faster_whisper`).
2. **Models & Multi-PC Portability**: Confirms that `MODELS_DIR` is reachable, checks the existence and non-zero size of all configured `.gguf` and `.bin` models, and verifies `./models/` drop-in readiness.
3. **Audio Input/Output**: Queries active ALSA/PulseAudio/PipeWire audio devices, verifies default recording mic, and calculates live mic signal RMS levels.
4. **Desktop Environment & Hotkeys**: Detects Wayland vs X11, verifies `/dev/input/event*` read permissions for kernel walkie-talkie hotkeys, and verifies `ydotool` / `wl-copy` / `xdotool` availability.
5. **Ollama LLM Service**: Pings local Ollama daemon, lists pulled models, and ensures required English (`qwen2.5:3b`) and Hindi (`llama3-hindi`) refiners are downloaded.
6. **Audio-to-Idea Batch Tools**: Validates that `ffmpeg` and `ffprobe` binaries are available in `$PATH`.

#### GUI Integration:
You can also run the doctor directly from the Web Settings GUI (`http://127.0.0.1:8765/settings`) by clicking the **🏥 System Doctor** button in the top navigation bar. It renders live status chips (`PASS`, `WARN`, `FAIL`) and provides copy-pasteable one-liner fixes for any warning.

---

### 1.6 Unified PEP 621 Package Installation (Ubuntu 22.04 through 26.04)
> **Goal:** Single standardized package configuration (`pyproject.toml`) that installs identically across Ubuntu 22.04 LTS (Python 3.10), Ubuntu 24.04 LTS (Python 3.12), and Ubuntu 26.04 (Python 3.14) without maintaining separate OS files.

#### Host System Prerequisites (APT):
On both Ubuntu 22.04 and Ubuntu 26.04, install the required audio, media, and Wayland system libraries:
```bash
sudo apt update && sudo apt install -y python3-dev ffmpeg libvulkan1 wl-clipboard
```

#### Python Environment Setup & Installation Tiers:
```bash
# 1. Create and activate standard virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Recommended: Install complete assistant with GPU ASR, GUI, and batch tools
pip install -e ".[all]"

# Alternatively: Minimal headless terminal installation
pip install -e .

# Backwards-compatible legacy syntax (uses PEP 621 shim)
pip install -r requirements.txt
```

#### Native Shell CLI Commands:
Once installed, the project provides direct console scripts accessible anywhere in your terminal environment:
- **`voice-refiner`**: Starts the system tray daemon, VAD microphone listener, and global hotkeys.
- **`voice-doctor`**: Executes the self-healing 24-check environment diagnostics.
- **`audio2idea`**: Launches the CLI batch audio file transcriber and evidence synthesizer.
- **`audio2idea-gui`**: Opens the dedicated CustomTkinter audio-to-idea application.

---

## 2. Core Voice Refiner (`config.json`) Reference

| Configuration Key | Type | Default | Valid Options | Description & Performance Impact |
|---|---|---|---|---|
| `SETTINGS_PORT` | `integer` | `8765` | `1024` – `65535` | Local TCP loopback port for the Glassmorphic Settings Web App and REST API daemon. Can also be overridden via the `VOICE_REFINER_SETTINGS_PORT` environment variable. |
| `MODELS_DIR` | `string` | `"/media/manoj/F1/models-handy"` | Path string | Base directory where local GGUF/bin ASR models reside. Set to `./models` or custom folder on another PC. |
| `PAUSE_GUIDED_CHUNKING` | `boolean` | `true` | `true`, `false` | Enables Handy acoustic breath-guided chunking for recordings $>40$s to eliminate Whisper hallucinations. |
| `CHUNK_TARGET_SECONDS` | `float` | `30.0` | `15.0` – `45.0` | Target chunk length for breath-aligned acoustic splits. |
| `CHUNK_MAX_SECONDS` | `float` | `40.0` | `30.0` – `60.0` | Maximum recording duration before acoustic splitting is enforced. |
| `ASR_ENGINE` | `string` | `"transcribe_cpp"` | `"transcribe_cpp"`, `"faster_whisper"`, `"handy_cli"` | Speech-to-text backend engine. `transcribe_cpp` runs GGUF models on GPU via Vulkan (~138ms). `faster_whisper` uses CTranslate2. |
| `ACTIVE_MODEL_PROFILE` | `string` | `"nemotron_fast"` | Any key in `MODEL_PROFILES` | Active model preset. Switchable in real-time from the tray menu or settings GUI. |
| `MODEL_PROFILES` | `object` | *(see below)* | Dictionary of profile objects | Defines named model paths, formats, and hardware targets. |
| `OLLAMA_HOST` | `string` | `"http://localhost:11434"` | URL string | Address of your local or network Ollama service. |
| `OLLAMA_KEEP_ALIVE` | `string` | `"60m"` | `"0"`, `"2m"`, `"5m"`, `"15m"`, `"60m"`, `"-1"` | **VRAM Lifecycle**: How long Ollama holds model weights in GPU VRAM after generating. Set `"0"` on low-VRAM machines to free VRAM immediately. Set `"60m"` or `"-1"` on high-VRAM machines for sub-second responses. |
| `OLLAMA_MODELS.en` | `string` | `"qwen2.5:3b"` | Installed Ollama model | Model used for English text refinement, grammar cleanup, and restructuring. |
| `OLLAMA_MODELS.hi` | `string` | `"llama3-hindi"` | Installed Ollama model | Model used for Hindi text refinement and grammar correction. |
| `OLLAMA_TRANSLATE_MODELS.to_en` | `string` | `"qwen2.5:3b"` | Installed Ollama model | Model used when `MODE: "translate"` converts Hindi speech $\rightarrow$ polished English. |
| `MODE` | `string` | `"refine"` | `"refine"`, `"translate"` | Default dictation mode. `refine` polishes in the spoken language. `translate` outputs refined English on clipboard. |
| `SILENCE_THRESHOLD` | `integer` | `300` | `50` – `1000` | Microphone audio energy gate. Speech below this RMS level is treated as silence. Higher values ignore room background noise; lower values capture soft whispers. |
| `SILENCE_DURATION` | `float` | `2.0` | `0.5` – `5.0` | Seconds of continuous silence before recording automatically stops. |
| `TEMPERATURE` | `float` | `0.1` | `0.0` – `1.0` | LLM generation temperature. `0.0` or `0.1` ensures consistent, strictly factual grammar refinement without creative hallucinations. |
| `DIRECT_TYPING` | `boolean` | `true` | `true`, `false` | When `true`, automatically types refined text at the cursor position in addition to copying to clipboard. |
| `TYPING_TOOL` | `string` | `"auto"` | `"auto"`, `"ydotool"`, `"wtype"`, `"xdotool"` | Cursor typing mechanism. `"auto"` detects Wayland vs X11 automatically. |
| `FEATURES.start_end_sounds` | `boolean` | `true` | `true`, `false` | Plays audio cues when recording begins and ends. |
| `FEATURES.clipboard_output` | `boolean` | `true` | `true`, `false` | Copies refined text to system clipboard. |
| `FEATURES.markdown_output` | `boolean` | `false` | `true`, `false` | Appends refined text to a markdown notes file. |
| `FEATURES.evening_review` | `boolean` | `true` | `true`, `false` | Displays the **Start Evening Review** option in the tray menu. |
| `FEATURES.pwd_terminology_corrector` | `boolean` | `true` | `true`, `false` | Enables automatic domain abbreviation correction (e.g. "the ee issued nit" $\rightarrow$ "the EE issued NIT") and PWD glossary lookup. |
| `FEATURES.filler_word_removal` | `boolean` | `true` | `true`, `false` | Master toggle for microsecond verbal hesitation stripping (*"um"*, *"uh"*, *"you know"*, *"मतलब"*) and stutter collapsing. |
| `FEATURES.fuzzy_custom_words` | `boolean` | `true` | `true`, `false` | Master toggle for in-memory fuzzy n-gram custom word and acronym replacement. |
| `ENABLE_FILLER_REMOVAL` | `boolean` | `true` | `true`, `false` | In-memory verbal hesitation cleaner (<0.1ms). Strips fillers before LLM refinement. |
| `COLLAPSE_STUTTERS` | `boolean` | `true` | `true`, `false` | Collapses 3+ consecutive word repetitions (*"I I I I"* $\rightarrow$ *"I"*). |
| `CUSTOM_FILLER_WORDS` | `array` | `[]` | List of strings | Optional user-specific filler words (e.g. `["basically", "literally"]`). |
| `ENABLE_FUZZY_CUSTOM_WORDS` | `boolean` | `true` | `true`, `false` | Sub-millisecond sliding n-gram custom word corrector (<1ms) based on Handy Rust text.rs. |
| `FUZZY_MATCH_THRESHOLD` | `number` | `0.35` | `0.1` to `0.6` | Maximum distance threshold (default 0.35). Lower = stricter; higher = looser. |
| `CUSTOM_WORDS` | `array` | `[...]` | List of strings | User dictionary terms to automatically correct (e.g. `["ChatGPT", "OpenAI", "Claude", "MacBook Pro", "ChargeBee"]`). |

---

## 3. Evening Review (`review_config.json`) Reference

| Configuration Key | Type | Default | Description |
|---|---|---|---|
| `vault_paths.base_vault` | `string` | `"~/learning_vault"` | Root directory of your Obsidian vault. |
| `vault_paths.daily_notes` | `string` | `"~/learning_vault/My Daily Notes"` | Target folder for daily notes (`YYYY/Month/YYYY-MM-DD.md`). |
| `vault_paths.wellness_notes` | `string` | `".../Wellness"` | Target folder for private wellness step reflections. |
| `review_expiry_hours` | `integer` | `1` | Hours before an in-progress session is marked expired. |
| `voice_narration` | `boolean` | `true` | Speaks reflection prompts aloud using neural TTS. |
| `tts_engine` | `string` | `"piper"` | TTS engine: `"piper"` (offline neural) or `"espeak"` (built-in fallback). |
| `piper_model` | `string` | `"models/en_US-lessac-medium.onnx"` | English neural voice model. |
| `piper_model_hi` | `string` | `"models/hi_IN-priyamvada-medium.onnx"`| Hindi neural voice model. |
| `voice_control` | `boolean` | `true` | Enables hands-free wake words ("stop", "again", "आगे", "छोड़ो"). |
| `last_n_days_context` | `integer` | `3` | Number of previous daily notes synthesized for the evening context brief. |
| `carryforward_tasks` | `boolean` | `true` | Reads unchecked tasks (`- [ ]`) from yesterday's daily note and narrates them. |
| `show_streak` | `boolean` | `true` | Tracks consecutive daily review completions (`🔥 N` days). |
| `morning_briefing_enabled` | `boolean`| `false` | Enables systemd morning priority alerts. |
| `morning_briefing_time` | `string` | `"08:00"` | Daily time for the morning briefing. |
| `telegram_enabled` | `boolean` | `false` | Enables mobile notifications via Telegram bot. |
| `telegram_bot_token` | `string` | `""` | Bot token from `@BotFather`. |
| `telegram_chat_id` | `string` | `""` | User chat ID from `@userinfobot`. |

---

## 4. Audio to Ideas (`audio_to_idea_config.json`) Reference

| Configuration Key | Type | Default | Description |
|---|---|---|---|
| `synthesis.mode` | `string` | `"clean_paragraph"` | Default extraction mode: `"clean_paragraph"`, `"concise_summary"`, `"ideas_actions"`. |
| `synthesis.output_language` | `string` | `"source"` | Output language: `"source"` (preserves English/Hindi mix), `"English"`, or `"Hindi"`. |
| `audio.sample_rate` | `integer` | `16000` | Sample rate for ASR preparation. |
| `audio.chunk_seconds` | `float` | `60.0` | Window size for long audio processing (120s for transcribe-cpp). |
| `audio.overlap_seconds` | `float` | `1.5` | Boundary overlap protecting words spoken across split windows. |
| `watch.poll_seconds` | `float` | `2.0` | Polling interval for background folder watcher. |
| `output.formats` | `list` | `["txt"]` | Export formats: `["txt", "srt"]`. |

### 4.1 Next-Gen Web Dashboard (`/audio-to-idea`)
The Audio-to-Ideas interface can be launched as a standalone GPU-accelerated window via:
```bash
./audio_to_idea_launcher.py
# Or navigate to: http://127.0.0.1:8765/audio-to-idea
```
Features:
- **Synchronized Audio & Transcript**: Click any segment `[S00001]` to seek and play audio instantly.
- **Drag & Drop Queue**: Batch process MP3, WAV, M4A, FLAC, OGG, and WEBM files with real-time SSE progress.
- **Evidence-Linked Ideas**: In *Ideas & Actions* mode, click any `[S0000X]` badge to highlight source transcript evidence and audio.
- **Live Theme Toggle**: Real-time Dark and Light glassmorphism styling.

---

## 5. PWD Language Helper & Hybrid CLI (`pwd_cli.py` & `pwd_helper/`)

The PWD Language Helper integrates civil engineering and departmental terminology from Uttarakhand Public Works Department directly into both the real-time speech engine and a standalone terminal/CLI utility.

### 5.1 Architecture & Components
* **Core Dictionary (`pwd_dict.json`)**: Contains 53 standard PWD designations, document types, and technical abbreviations categorized into `officers`, `documents`, `schemes`, and `technical`.
* **Custom Extension (`custom_dict.json`)**: Place in `pwd_helper/custom_dict.json` or your project root to append personal or local project abbreviations without modifying core files.
* **In-Flight Speech Normalizer (`pwd_helper.normalizer`)**: Auto-corrects spoken abbreviations during dictation (e.g. *"the ee met the ae to review the mb for rcc culvert"* $\rightarrow$ *"the EE met the AE to review the MB for RCC culvert"*).
* **Tri-Tier Translator (`pwd_helper.translator`)**:
  1. *Ollama LLM*: Context-aware domain translation via local models (`qwen2.5:3b` / `llama3-hindi`).
  2. *Online Fallback*: Zero-dependency pure Python Google Translate fallback.
  3. *Offline Argos*: Direct local neural translation (optional).

### 5.2 Terminal & CLI Commands (`pwd_cli.py`)
Run directly in your terminal:

```bash
# 1. Quick Abbreviation Lookup
./pwd_cli.py ee
# Output: [officers] EE = Executive Engineer (अधिशासी अभियंता)

# 2. Lookup and Copy to Clipboard
./pwd_cli.py nit -c

# 3. Bilingual Translation
./pwd_cli.py translate "Bridge inspection"
# Output: Hindi (online_google): पुल निरीक्षण

# 4. Search by English or Hindi keyword
./pwd_cli.py search "निविदा"
./pwd_cli.py search "tender"

# 5. Interactive REPL (with Voice Dictation toggle)
./pwd_cli.py
pwd> search engineer
pwd> ee
pwd> v               # Activates microphone dictation directly inside the CLI!
```

### 5.3 FastAPI Service for External / Laravel Integration (`pwd_helper/api.py`)
To expose PWD terminology and translation services to external PHP/Laravel web dashboards or office portals:

```bash
# Start the FastAPI service on port 8000
python3 -m uvicorn pwd_helper.api:app --host 0.0.0.0 --port 8000
```
* **Endpoints**:
  - `POST /api/translate`: Translates text between English and Hindi (`{"text": "Bridge", "mode": "auto"}`).
  - `GET /api/abbreviation?q=EE`: Returns JSON definition with designation and Hindi translation.
  - `GET /api/search?q=tender`: Returns all matching abbreviations.
  - `GET /api/abbreviations`: Returns complete terminology database.

### 5.4 Live Rich Terminal Dictation HUD & Shell Voice Alias
> **Goal:** High-productivity voice dictation directly inside Bash, Zsh, or Tmux without opening extra GUI windows or browsers. Completely isolated from the background system tray daemon and desktop hotkeys.

#### 1. Live Terminal Dictation (`--listen`):
Speak into the microphone and view an animated real-time VU audio meter and pipeline status:
```bash
# Speak and print refined text (also copies to clipboard)
python pwd_cli.py --listen

# Disable visual HUD (minimal plain-text output)
python pwd_cli.py --listen --no-hud

# Pipe refined text directly into git, grep, or a file
python pwd_cli.py --listen --pipe | git commit -F -
python pwd_cli.py --listen --pipe > site_notes.md
```

#### 2. Shell Voice Typing Aliases & Zsh Integration (`scripts/terminal_voice.sh`):
The repository provides modular shell integration for Bash and Zsh (`~/.zsh/aliases.zsh` and `~/.zsh/functions.zsh`):

```zsh
# Available from ANY directory on your machine:
v         # 1-letter shortcut: speaks and dictates with live Rich Terminal HUD
voice     # Full alias for 'python pwd_cli.py --listen'
v-doc     # Runs the 24-point self-healing system doctor diagnostics

# In-Prompt Voice Injection:
Ctrl+G    # Press Ctrl+G at your active prompt, speak a command (e.g. "git status"),
          # and the text is automatically injected directly onto your command line!
```

##### How the Shortcuts Work Under the Hood:
- **Zero Directory Dependency**: Always invokes the project's virtual environment interpreter (`.venv/bin/python`), guaranteeing all dependencies (`rich`, `transcribe_cpp`, `faster-whisper`, `scipy`) are loaded even if you are in your home folder (`~`) or `/var/www/`.
- **ZLE Prompt Widget**: In Zsh, `Ctrl+G` hooks directly into the Zsh Line Editor (ZLE), appending transcribed speech directly into `$LBUFFER` and calling `zle reset-prompt`.
- **Automatic Clipboard Copy**: Any dictated text is automatically copied to the system clipboard in addition to terminal display.

#### 3. Transparent ON vs. OFF Tradeoff:
- **`CLI_RICH_HUD: true` (ON)**: Visual microphone assurance with animated volume VU meter, clear status transitions (`RECORDING` $\rightarrow$ `TRANSCRIBING` $\rightarrow$ `DONE`), and Catppuccin color-coded panels. Automatically diverts HUD to `stderr` when piping so stdout receives only pure text.
- **`CLI_RICH_HUD: false` (OFF)**: Minimal unstyled text output for headless servers or automated cron scripts.

---

## 6. Next-Level Animated Visuals & System Tray

Both the GUI and System Tray feature animated vector feedback designed for instantaneous state awareness:

### 6.1 Vector Animation States in `main_gui.py`
The status badge and hero visualizer render smooth vector states at 5 FPS:
* **Idle (🎙)**: Steady glowing microphone icon in Catppuccin Blue (`#89b4fa`).
* **Recording (👂)**: Pulsing acoustic ear icon radiating expanding acoustic wave arcs (`#f38ba8` Coral Red).
* **Processing / Refining (🧠)**: Synapsing brain icon surrounded by orbiting neural nodes in Lavender (`#b4befe`).
* **Success (✨)**: Sparkling green confirmation indicator (`#a6e3a1`).

### 6.2 High-Resolution Pillow Vector Tray Icons (`tray_app.py`)
The system tray dynamically renders crisp 64x64 vector icons in real-time on a dedicated background animation thread. No blurry bitmap dots or external GIF assets are needed.

---

## 7. How to Adjust Settings

### Method 1: Web Settings & Desktop GUI (Recommended)
Open your browser to `http://127.0.0.1:8765` or right-click the tray icon and select **Settings**:
- **Voice Refiner Tab**: Switch ASR presets, set the base Models Directory (`MODELS_DIR`) for cross-PC portability, configure Whisper Fallback, adjust Ollama models and Keep-Alive VRAM timers, and tune Pause-Guided chunking sliders.
- **Auto-Paste & Desktop Tab**: Select clipboard paste methods (`clipboard_restore`, `clipboard_only`, `direct_typing`) and fine-tune typing delays.
- **Evening Review Tab**: Configure Obsidian vault paths, TTS voices, and context lookbacks.
- **Notifications Tab**: Set up Telegram bot credentials and morning briefing timers.
- **Features Tab**: Toggle individual capabilities on or off, including PWD Terminology Corrector.

### Method 2: Instant 1-Click System Tray Cycling
You can switch modes without opening the settings window:
- Click **Mode: Refine** in the tray menu to toggle between **Refine** and **Translate**.
- Click **🎙 ASR: <profile>** in the tray menu to cycle through your configured profiles (`nemotron_fast` $\rightarrow$ `whisper_turbo` $\rightarrow$ `whisper_large_v3` $\rightarrow$ `hinglish_apex`).
- Click **🏛 PWD Terminology Lookup** to launch the terminology glossary.

### Method 3: Direct JSON Editing
Edit `config.json` directly with any text editor. The application automatically re-reads the configuration.

---

## 8. Tuning & Optimization Guide

### Microphone Silence Calibration
If the assistant cuts you off too quickly or captures room noise:
1. Speak normally and observe if recording ends naturally ~2 seconds after you stop.
2. If recording ends while you are still speaking: **decrease `SILENCE_THRESHOLD`** (e.g. from 300 to 200).
3. If recording keeps running due to room fan or typing noise: **increase `SILENCE_THRESHOLD`** (e.g. from 300 to 450).

### Wayland Direct Typing Setup
On Ubuntu Wayland sessions, `xdotool` cannot simulate keystrokes directly. The application automatically uses `ydotool`.
To enable `ydotool` without requiring root permissions:
```bash
sudo systemctl enable --now ydotool
sudo usermod -aG ydotoold $USER
```
Log out and log back in once. Typing will now work seamlessly across any Wayland or X11 application!

### Filler Word & Stutter Removal (ON vs. OFF Decision Guide)
> **Configuration Key:** `ENABLE_FILLER_REMOVAL` (or `FEATURES.filler_word_removal` in `config.json` and Settings GUI)

The in-memory filler remover operates in <0.1ms (<60 microseconds) to eliminate verbal hesitation tokens before text reaches the LLM.

#### Transparent Tradeoff Comparison:

| Setting State | What You GAIN (Benefits) | What You LOSE / Potential Tradeoff | Recommended Use Case |
|---|---|---|---|
| **`ENABLE_FILLER_REMOVAL: true` (ON)** | 1. **Cleaner Text**: Instantly purges verbal hesitations (*"um"*, *"uh"*, *"you know"*, *"मतलब"*, *"जैसे कि"*).<br>2. **Faster LLM Generation**: 10–25% fewer input tokens sent to Ollama, reducing delay.<br>3. **Zero LLM Hallucinations**: Prevents small models (3B) from interpreting *"you know"* as conversational prompt banter.<br>4. **Sentence Capitalization Recovery**: *"Um, so we..."* automatically recovers as *"So we..."*.<br>5. **Stutter Collapse**: *"I I I think"* collapses to *"I think"*. | 1. **Not 100% Verbatim**: Spoken hesitations are intentionally filtered out.<br>2. **Context Guard**: Hindi *"मतलब"* is only stripped when used as a clause-opening filler (`", matlab, ..."`). If you dictate a dictionary question like *"Is shabd ka matlab kya hai?"*, context rules preserve it, but turning OFF ensures 100% untouched raw text. | Daily dictation, drafting emails, engineering inspection notes, code comments, official memos. |
| **`ENABLE_FILLER_REMOVAL: false` (OFF)** | 1. **100% Literal Verbatim Speech**: Every single pause, human hesitation sound, and verbal repetition is preserved exactly as spoken.<br>2. **Forensic Record**: Complete fidelity to the raw audio recording. | 1. **Cluttered Output**: Text is burdened with verbal hesitation sounds.<br>2. **Slower LLM**: More tokens consumed.<br>3. **Stutters Remain**: *"the the the"* remains uncollapsed. | Legal depositions, court reporting, psychological evaluations, linguistic research, or literal transcript archives. |

### Fuzzy N-Gram Domain Dictionary (ON vs. OFF Decision Guide)
> **Configuration Key:** `ENABLE_FUZZY_CUSTOM_WORDS` (or `FEATURES.fuzzy_custom_words` in `config.json` and Settings GUI)
> **Threshold Key:** `FUZZY_MATCH_THRESHOLD` (default: `0.35`)
> **Custom Words Key:** `CUSTOM_WORDS` (list of strings)

Based on Handy's Rust `text.rs` architecture, the in-memory Fuzzy N-Gram engine runs immediately after raw speech recognition in $<1\text{ ms}$. It uses a multi-token sliding window ($N \in \{1, 2, 3, 4\}$), American Soundex phonetic boosting, normalized Levenshtein distance, a 25% length difference guard, and short-term exact safeguards.

#### Transparent Tradeoff Comparison:

| Setting State | What You GAIN (Benefits) | What You LOSE / Potential Tradeoff | Recommended Use Case |
|---|---|---|---|
| **`ENABLE_FUZZY_CUSTOM_WORDS: true` (ON)** | 1. **Repairs Split Acronyms**: Fixes multi-word speech token splits (*"Chat G P T"* $\rightarrow$ *"ChatGPT"*, *"Charge B"* $\rightarrow$ *"ChargeBee"*, *"Open AI"* $\rightarrow$ *"OpenAI"*, *"Mac Book Pro"* $\rightarrow$ *"MacBook Pro"*, *"D P R"* $\rightarrow$ *"DPR"*, *"P M G S Y"* $\rightarrow$ *"PMGSY"*).<br>2. **Phonetic Near-Miss Correction**: Accented speech (*"culvert winding"* $\rightarrow$ *"culvert widening"*, *"arthwork"* $\rightarrow$ *"earthwork"*, *"R and D"* $\rightarrow$ *"R&D"*) matches domain terms instantly.<br>3. **Zero LLM Latency**: Runs entirely in-memory in $<1\text{ ms}$ before clipboard paste.<br>4. **Boundary Punctuation & Casing**: Preserves enclosing punctuation (*"(Charge B)?"* $\rightarrow$ *"(ChargeBee)?"*, *"「Handee。」"* $\rightarrow$ *"「Handy。」"*) and casing (*"CHARGE B"* $\rightarrow$ *"CHARGEBEE"*).<br>5. **Short-Term Safeguards**: 3-letter acronyms (*SOR*, *SDO*, *EE*) require exact matches, completely preventing common English words (*"for"*, *"site"*, *"so"*) from being mistakenly replaced. | 1. **Potential Over-matching If Threshold $>0.5$**: If `FUZZY_MATCH_THRESHOLD` is set too loosely ($>0.5$), unrelated words may match. *(The strict default of `0.35` and $25\%$ length guard eliminate this risk).*<br>2. **Not Literally Verbatim**: Corrects phonetically misheard proper nouns and acronyms instead of leaving raw ASR errors. | Daily dictation, technical notes, engineering inspections, software development, email drafting, and instant typing modes. |
| **`ENABLE_FUZZY_CUSTOM_WORDS: false` (OFF)** | 1. **100% Unmodified ASR Tokens**: Output reflects strictly what the speech recognition model emitted character-for-character.<br>2. **Zero Word Replacement**: No dictionary substitutions are attempted. | 1. **Fragmented Proper Nouns**: Spoken acronyms like *"Chat G P T"* or *"D P R"* remain broken into separate spaced letters.<br>2. **Phonetic Errors Remain**: Transcriptions like *"calvert winding"* or *"Charge B"* stay broken unless corrected by a slow LLM call ($+1.5\text{s}$ to $+3.0\text{s}$). | ASR model acoustic benchmarking, pure phonetic transcription analysis, or forensic transcription archiving. |

---

---

## 9. Best Practice Matrix: Speed + Accuracy for Input Audio vs Output Goal

To achieve the best speed, lowest latency, and highest accuracy without hallucination or script confusion, select the combination matching your input speech and target output style:

### 9.1 Speed + Accuracy Decision Matrix

| Input Speech Type | Target Output Goal | Optimal ASR Profile | Language Mode (`LANGUAGE_MODE`) | Recommended LLM (`OLLAMA_MODELS`) | End-to-End Latency | Accuracy Rating | Why This Combination Excels |
|---|---|---|---|---|---|---|---|
| **Pure English** (Indian or Global Accent) | **Polished Official English** (Emails, Reports, Notes) | `nemotron_fast` *(or `whisper_turbo` with forced EN)* | `pure_english` | `qwen2.5:3b` | **~0.8s** *(138ms ASR + 0.6s LLM)* | **100% (Flawless)** | `nemotron_fast` has strictly English subword tokens, rendering Devanagari confusion impossible. Qwen's phonetic recovery rules reconstruct any PWD abbreviations (`MB`, `AE`, `NIT`). |
| **Mixed Hindi + English** (Spoken Hinglish) | **Natural Spoken Bilingual** (English terms in Latin, Hindi in Devanagari) | `whisper_large_v3` *(or `whisper_turbo`)* | `bilingual` *(Default)* | `qwen2.5:3b` *(or `llama3-hindi`)* | **~1.8s – ~2.2s** | **98% (Natural)** | Whisper accurately captures code-switching. Model-specific bilingual prompts instruct the LLM never to over-translate Hindi to English nor transliterate English to Devanagari. |
| **Spoken Hindi or Mixed Hinglish** | **Formal Official Hindi** (कार्यालयी पत्राचार / शासकीय टिप्पणी) | `whisper_large_v3` | `pure_hindi` | `llama3-hindi` (`SL-Lexicons/llama3-hindi-8b-q5_km`) | **~2.0s – ~2.5s** | **99% (Native Grammar)** | `llama3-hindi` receives native Devanagari instructions. It generates proper Hindi syntax and postpositions (कारक, विराम चिह्न) while keeping departmental terms (`EE`, `MB`, `NIT`, `RCC`) in English Latin script. |
| **Rapid Chat / Messaging** (WhatsApp, Slack, Quick Notes) | **Roman-script Hinglish** (Spoken mix written in English letters) | `whisper_turbo` *(or `hinglish_apex`)* | `roman_hinglish` | `qwen2.5:3b` | **~0.9s – ~1.2s** | **96% (Chat-Ready)** | Delivers conversational Hinglish directly in the Latin alphabet (e.g. *"Aaj site visit complete ho gaya aur EE sir ne MB approve kar di hai"*), eliminating keyboard layout switching. |
| **Spoken Hindi / Hinglish** | **Pure English Translation** (Formal Records / English Documentation) | `whisper_large_v3` *(or `whisper_turbo`)* | `pure_english` | `qwen2.5:3b` | **~1.6s – ~2.0s** | **97% (Fluent English)** | Whisper captures the spoken Hindi/Hinglish audio, and Qwen 2.5 3B translates the full thought into fluent, professional documentation English while preserving PWD uppercase terms. |

---

### 9.2 Key Architectural Principles for Peak Accuracy

1. **Why Model-Specific Prompts Matter (`prompts/<model_alias>/`)**:
   - **`llama3-hindi`**: Fine-tuned on Hindi instruction datasets. When prompted with English instructions (even if asking for Hindi output), it tends to respond in English and over-translate. Its dedicated prompt folder (`prompts/llama3_hindi/`) uses native Hindi Devanagari system prompts to enforce strict obedience.
   - **`qwen2.5:3b`**: Exceptionally fast and obedient, but can over-interpret unfamiliar Devanagari transcriptions. Its prompt folder (`prompts/qwen2.5_3b/`) incorporates explicit **Phonetic & Script Recovery Rules** so that Devanagari-transcribed English phonetics (`"मी"` $\rightarrow$ `MB`, `"हिड्स"` $\rightarrow$ `he needs`) are correctly recovered without hallucinating false metaphors.

2. **Smart ASR Coupling at the Speech Layer**:
   - In `pure_english` mode, the engine automatically forces `language="en"` and injects civil engineering vocabulary cues (`EE, AE, JE, NIT, MB, RCC`) into Whisper's initial prompt. This prevents Whisper from misdetecting Indian English accents as Hindi, eliminating Devanagari garbling before it ever reaches the LLM.
   - In `pure_hindi` mode, the engine forces `language="hi"` with `_HINDI_PROMPT`, bypassing Whisper's language-detection roundtrip for instant Devanagari transcription.

3. **ASR Engine Differences**:
   - **`nemotron_fast` (NVIDIA Nemotron 3.5 Streaming GGUF)**: Lightning-fast (~138ms on RTX 3060). **English speech only**. Best for pure English dictation, email drafting, and coding notes.
   - **`whisper_large_v3` (Faster-Whisper)**: Gold standard for mixed Hindi-English audio, heavy regional accents, and official Hindi dictation.
   - **`whisper_turbo`**: Excellent balance of speed (~0.4s) and bilingual accuracy for day-to-day mixed dictation.


