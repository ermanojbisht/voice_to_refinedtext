# AI Voice Refiner, Audio to Ideas & PWD Helper — Master Concept & Roadmap

## 1. System Overview & Core Architecture

This repository is a local, privacy-first voice-to-text, terminology normalization, and AI-assisted workflow system built for Linux (Ubuntu desktop). It captures speech, transcribes it locally, refines or synthesizes it using local LLMs (via Ollama), normalizes departmental domain terms (PWD Uttarakhand), and delivers polished output directly to the desktop (system clipboard, cursor typing, terminal REPL, or Obsidian daily notes).

### Subsystems Breakdown

```
                              ┌──────────────────────────────────────────────┐
                              │               Input Modalities               │
                              │   Microphone / Hotkey / Folder / CLI / Audio │
                              └──────────────────────┬───────────────────────┘
                                                     │
         ┌───────────────────────────┬───────────────┴───────────────┬───────────────────────────┐
         ▼                           ▼                               ▼                           ▼
┌──────────────────┐       ┌──────────────────┐            ┌──────────────────┐        ┌──────────────────┐
│ 1. Voice Refiner │       │ 2. Evening Review│            │ 3. Audio to Ideas│        │ 4. PWD Helper/CLI│
│ (Quick Dictation)│       │ (Daily Reflection│            │ (Batch & Archive)│        │(Domain Term Engine)
├──────────────────┤       ├──────────────────┤            ├──────────────────┤        ├──────────────────┤
│• System tray app │       │• Multi-step flow │            │• Dedicated GUI   │        │• Terminal REPL   │
│• Silence / VAD   │       │• Piper TTS voice │            │• Multi-file merge│        │• One-shot lookup │
│• Transcribe-cpp  │       │• Wake-word ctrl  │            │• Timestamps/SRT  │        │• In-flight normal│
│• Ollama refine   │       │• Obsidian sync   │            │• Folder watcher  │        │• Bilingual trans │
│• Direct typing   │       │• Telegram alerts │            │• Evidence cites  │        │• FastAPI / Laravel│
└──────────────────┘       └──────────────────┘            └──────────────────┘        └──────────────────┘
```

1. **Core Voice Refiner (`engine.py`, `tray_app.py`, `main_gui.py`, `config_gui.py`)**:
   - Push-to-talk / global hotkey (`Ctrl+Alt+V`) and background system tray indicator.
   - High-speed ASR (`transcribe_cpp` running Nemotron 0.6B Q8_0 GGUF on Vulkan in ~138ms).
   - In-flight PWD terminology auto-casing and expansion.
   - Ollama grammar cleanup and bilingual translation.
   - Direct cursor typing (`ydotool` on Wayland, `xdotool` on X11) and clipboard insertion.

2. **Evening Review & Daily Reflection (`review_engine.py`, `review_dashboard.py`)**:
   - Guided multi-step evening reflection (Focus Word, Achievements, Priorities, Wellness, Meetings).
   - Voice narration via `piper` neural TTS (or `espeak-ng`).
   - Hands-free wake-word control ("stop", "again", "आगे", "छोड़ो").
   - Direct synchronization with Obsidian daily notes (`YYYY/Month/YYYY-MM-DD.md`).
   - Carry-forward task detection (`- [ ]`), streak counter (`streak.json`), and Telegram alerts.

3. **Audio to Ideas Module (`audio_to_idea/`)**:
   - Batch audio file and folder processor with dedicated CustomTkinter GUI and CLI.
   - Processing modes: *Clean paragraph* (default), *Concise summary*, *Ideas & actions*.
   - Multi-file synthesis and cross-clip deduplication with evidence timestamp citations.
   - Background folder watcher with lockfiles, crash recovery checkpoints, and atomic writes.

4. **PWD Language Helper & Hybrid CLI (`pwd_helper/`, `pwd_cli.py`)**:
   - 53 departmental abbreviations and technical civil engineering terms.
   - Pure Python zero-dependency bilingual translation (Ollama + Google Translate fallback).
   - Terminal REPL with instant microphone voice dictation toggle (`v`).
   - FastAPI REST endpoints (`/api/translate`, `/api/abbreviation`, `/api/search`) for Laravel web apps.

---

## 2. In-Depth Study & Design Patterns Learned from Handy

Through complete inspection of `/media/manoj/datadisk_linux/pythonprojects/Handy` (`src-tauri/src/`), we extracted key architectural patterns that can elevate our Python architecture:

### 2.1 Audio Capture & Ring Buffer (`audio_toolkit/audio/sink.rs`)
* **Problem in Current Python Setup**: Simple RMS energy thresholding starts recording only *after* audio crosses a threshold. The first 100–300 ms (often the first consonant or syllable of a word) is vulnerable to truncation.
* **Handy's Solution**:
  - Implements a continuous circular ring buffer (`extra_recording_buffer_ms`, default 500ms).
  - Maintains `withheld_frames` with an `onset_counter` and `hangover_counter`.
  - When speech is detected, the preceding 500ms from the ring buffer is prepended to the recording chunk. This guarantees zero syllable clipping.

### 2.2 Noise-Resilient VAD with Silero v5 (`audio_toolkit/vad/silero.rs`)
* **Current Setup**: Simple RMS amplitude gate (`energy < threshold`). In environments with fan hum, laptop keyboard clicks, or distant speech, RMS falsely triggers or hangs.
* **Handy's Solution**:
  - Silero VAD operates on 512-sample (32ms at 16kHz) frames via ONNX runtime or GGML.
  - Generates probability scores (0.0 to 1.0) with hysteresis (`THRESHOLD: 0.5`, `NEG_THRESHOLD: 0.35`).
  - Distinguishes background ambient acoustics from actual vocal tract harmonics.

### 2.3 Pause-Guided Long Audio Chunking (`audio_toolkit/chunking.rs`)
* **Problem**: Speech models (especially Whisper) hallucinate or repeat loops when fed continuous audio chunks longer than 30–40 seconds.
* **Handy's Solution**:
  - Dynamically cuts audio only during detected acoustic pauses (> 250ms silence).
  - Targets chunks of 30.0 seconds with a minimum chunk of 5.0s and maximum of 40.0s.
  - Includes a 5.0-second lookahead so sentence mid-points are never severed.

### 2.4 Microsecond Filler Word Stripping (`audio_toolkit/text.rs`)
* **Problem**: Relying solely on an LLM to remove filler words ("um", "uh", "you know", "मतलब", "जैसे कि") wastes GPU tokens, adds latency, and occasionally alters meaning.
* **Handy's Solution**:
  - Pure in-memory regex and token trie stripping with language evidence gating.
  - Multi-word N-gram matching: handles fragmented transcriptions (e.g. `"Chat G P T"` $\rightarrow$ `"ChatGPT"`, `"Charge B"` $\rightarrow$ `"ChargeBee"`).
  - Uses phonetic Soundex and Levenshtein distance with a configurable confidence threshold.

### 2.5 Safe Linux Wayland/X11 Clipboard Pasting (`clipboard.rs`)
* **Problem**: Typing via simulated keyboard (`xdotool` / `ydotool type`) is slow for multi-paragraph text and can drop characters if typing speed exceeds buffer. Direct clipboard overwrite wipes out the user's previously copied text.
* **Handy's Solution**:
  - **Save & Restore Pattern**:
    1. Reads and saves current clipboard contents.
    2. Writes refined text to clipboard.
    3. Emits `Ctrl+V` (or `Shift+Insert` for terminals).
    4. Sleeps 100ms for active application to consume the event.
    5. Restores original clipboard contents so user clipboard history remains intact.

### 2.6 Key Activation & Debouncing (`transcription_coordinator.rs`)
* **Problem**: Linux X11 synthesizes artificial auto-repeat key-up / key-down events when holding a key down.
* **Handy's Solution**:
  - `RELEASE_GRACE` (50ms): key-up is deferred by 50ms. If an auto-repeat press arrives within that window, it is recognized as a continuous hold.
  - `HoldOrToggle` mode: Press and release quickly (< 300ms) toggles continuous recording; press and hold (> 300ms) acts as push-to-talk, automatically stopping upon release.

---

## 3. Performance Telemetry & Cold-Start Analysis

### 3.1 Live Hardware Benchmark (NVIDIA RTX 3060 12GB — Vulkan)
* **ASR Load Time**: 0.36 seconds
* **ASR Inference Speed**: **0.142s** for a 9.6s audio clip (**~67.4x real-time**) with `nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf`
* **VRAM Footprint**: ~800 MB (leaves >10 GB headroom for Ollama LLMs)
* **LLM Refine Speed**: ~200ms with `qwen2.5:3b`

### 3.2 Cold-Start Breakdown & Root Cause
Live telemetry identified that the first dictation takes ~33s, while all subsequent dictations take <0.5s:
| Stage | First Audio (Cold) | Subsequent Audios (Warm) | Cause |
| :--- | :---: | :---: | :--- |
| **ASR Shader JIT** | ~15.0s | ~0.14s | Vulkan compute pipeline initial shader compilation |
| **Ollama Model Load** | ~18.0s | ~0.25s | Reading 3GB model weights from NVMe into GPU VRAM |
| **Total Latency** | **~33.0s** | **~0.45s** | Cold load overhead |

---

## 4. Master Consolidated TODO Roadmap

The following categorized tracks represent our concrete implementation plan. Each track is structured with actionable, self-contained items.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MASTER TODO TRACKS                                │
├───────────────────────────────────┬─────────────────────────────────────────┤
│ Track A: Audio Capture & VAD      │ Track B: GUI & Animated Visuals         │
│ • Pre-speech ring buffer          │ • Floating minimal pill overlay         │
│ • Silero VAD v5 ONNX integration  │ • Real-time live audio waveform visual  │
│ • Pause-guided long audio chunker │ • Catppuccin theme unification          │
├───────────────────────────────────┼─────────────────────────────────────────┤
│ Track C: Text & Terminology       │ Track D: Desktop & System Integration   │
│ • Microsecond filler word remover │ • Clipboard save & restore auto-paste   │
│ • Fuzzy N-gram custom dictionary  │ • Hold-or-toggle hotkey with X11 grace  │
│ • Roman Hinglish Apex model setup │ • Pre-warm background daemon thread     │
├───────────────────────────────────┼─────────────────────────────────────────┤
│ Track E: Dual-PC Portability      │ Track F: Terminal & CLI Superpowers     │
│ • One-click `doctor.py` diagnoser │ • Live Rich terminal dictation HUD      │
│ • Low-VRAM dynamic profile sync   │ • Direct bash/zsh shell voice pipe      │
│ • Single pyproject.toml migration │ • Laravel / FastAPI web hooks           │
└───────────────────────────────────┴─────────────────────────────────────────┘
```

---

### Track A: Audio Capture & Resilient VAD Engine

#### [TODO-A1] Pre-Speech Audio Ring Buffer
* **Objective**: Eliminate first-syllable clipping when user starts speaking immediately upon hotkey press.
* **Technical Design**:
  - Implement a `CircularAudioBuffer(duration_ms=600, sample_rate=16000)` using `collections.deque` or NumPy ring buffer.
  - Background audio capture continuously feeds the ring buffer.
  - When recording starts, prepend the buffered pre-speech audio to the recording stream.
* **Target Files**: `engine.py`, `audio_to_idea/audio.py`
* **Complexity**: Medium | **Impact**: High (immediate audio quality improvement)

#### [TODO-A2] Silero VAD v5 ONNX Integration
* **Objective**: Replace simple RMS energy thresholding with neural voice activity detection.
* **Technical Design**:
  - Use `onnxruntime` with `silero_vad.onnx` (~2MB model).
  - Feed 512-sample (32ms) frames to determine speech probability.
  - Stop recording only when silence probability exceeds 0.65 for `SILENCE_DURATION` seconds.
  - Filter out typing noise, fan hum, and room acoustics.
* **Target Files**: `vad.py` (new), `engine.py`, `config.json`
* **Complexity**: Medium | **Impact**: High (robustness in noisy environments)

#### [TODO-A3] Pause-Guided Long Audio Chunker for Audio to Ideas
* **Objective**: Enable flawless batch processing of 30–120 minute audio files without Whisper hallucinations.
* **Technical Design**:
  - Port `chunking.rs` pause-guided cutting logic.
  - Scan audio for pauses > 250ms within 25–35 second windows.
  - Pass clean natural sentence chunks to `transcribe_cpp` (Nemotron runs at 67x real-time).
* **Target Files**: `audio_to_idea/chunking.py` (new), `audio_to_idea/transcription.py`
* **Complexity**: Medium | **Impact**: High (long-form audio reliability)

---

### Track B: GUI & Animated Visuals

#### [TODO-B1] Floating Minimal Pill Overlay Widget
* **Objective**: Provide a non-intrusive, always-on-top desktop pill showing live voice state without needing full window open.
* **Technical Design**:
  - Lightweight transparent Tkinter / PyQt window (`-topmost`, `-type splash`).
  - Positions at screen top-center or bottom-right.
  - Displays dynamic state icons:
    - `🎙 Idle` (dim blue)
    - `👂 Listening... [Waveform]` (pulsing red)
    - `🧠 Thinking...` (spinning lavender)
    - `✨ Pasted` (green check)
  - Auto-hides 1.5 seconds after pasting.
* **Target Files**: `overlay_gui.py` (new), `tray_app.py`, `config_gui.py`
* **Complexity**: Medium | **Impact**: Very High (modern, polished desktop feel)

#### [TODO-B2] Real-Time Live Audio Waveform Canvas in Main GUI
* **Objective**: Replace static status icons with a fluid, reacting audio waveform during recording.
* **Technical Design**:
  - Sample mic RMS levels every 50ms during active recording.
  - Render an 8-bar or 12-bar bouncing equalizer or smooth bezier wave on `main_gui.py` canvas.
* **Target Files**: `main_gui.py`, `theme.py`
* **Complexity**: Low-Medium | **Impact**: High (matches Text-to-Audio visual quality)

#### [TODO-B3] Unified Catppuccin Theme System
* **Objective**: Ensure complete design and color palette consistency between `main_gui.py`, `config_gui.py`, and `audio_to_idea/gui.py`.
* **Technical Design**:
  - Export standard color constants from `theme.py` (`MOCHA_CRUST`, `MOCHA_BASE`, `MOCHA_SURFACE`, `MOCHA_TEXT`, `CAT_ACCENT_BLUE`, `CAT_CORAL_RED`).
  - Standardize glass card borders (`#363a4f`), dark wells (`#181825`), and pill buttons.
* **Target Files**: `theme.py`, `audio_to_idea/gui.py`, `main_gui.py`
* **Complexity**: Low | **Impact**: Medium (visual excellence)

---

### Track C: Text Pipeline, Filler Removal & Custom Glossary

#### [TODO-C1] Microsecond In-Memory Filler Word Remover
* **Objective**: Strip hesitation sounds (*"um"*, *"uh"*, *"you know"*, *"मतलब"*, *"जैसे कि"*) instantaneously before sending to LLM.
* **Technical Design**:
  - Implement a fast regex/trie filter in `pwd_helper/filler.py`.
  - Language-gated profiles (English, Hindi, Hinglish).
  - Saves LLM compute tokens, prevents hallucinations, and speeds up dictation.
* **Target Files**: `pwd_helper/filler.py` (new), `engine.py`, `config.json`
* **Complexity**: Low | **Impact**: High (cleaner output, faster LLM)

#### [TODO-C2] Fuzzy N-Gram Custom Domain Replacement Engine
* **Objective**: Auto-correct split or phonetically misrecognized domain terms (e.g. *"Charge B"* $\rightarrow$ *"ChargeBee"*, *"Chat G P T"* $\rightarrow$ *"ChatGPT"*, *"D P R"* $\rightarrow$ *"DPR"*).
* **Technical Design**:
  - Port `text.rs` multi-word n-gram matcher using Soundex / Levenshtein distance.
  - Match against `custom_words.json` and `pwd_dict.json`.
* **Target Files**: `pwd_helper/custom_matcher.py` (new), `engine.py`
* **Complexity**: Medium | **Impact**: High (domain precision)

#### [TODO-C3] Roman-Script Hinglish Apex Model Integration
* **Objective**: Allow users to dictate in natural conversational Hindi and output clean Roman/Latin script (*"kya haal hai"* instead of Devanagari *"क्या हाल है"*).
* **Technical Design**:
  - Configure `Whisper-Hindi2Hinglish-Apex-Q8.bin` profile in `MODEL_PROFILES`.
  - Add download/setup script in `scripts/download_hinglish.sh`.
* **Target Files**: `config.json`, `docs/setup_guide.md`
* **Complexity**: Low | **Impact**: High for users preferring Roman-script Hindi

---

### Track D: Desktop & System Integration

#### [TODO-D1] Clipboard Save & Restore Auto-Pasting
* **Objective**: Auto-paste refined text into the active window upon recording completion, while preserving the user's existing clipboard history.
* **Technical Design**:
  - Save current clipboard text via `pyperclip` or `wl-paste` / `xclip`.
  - Copy refined text to clipboard.
  - Emit paste key event (`Ctrl+V` or `Ctrl+Shift+V` if terminal) via `ydotool` / `xdotool`.
  - Wait 100ms, then restore the saved original clipboard content.
* **Target Files**: `engine.py`, `utils.py`, `config.json`
* **Complexity**: Low-Medium | **Impact**: Very High (workflow convenience)

#### [TODO-D2] Hold-or-Toggle Hotkey Mode with Linux X11 Auto-Repeat Suppression
* **Objective**: Support both Push-to-Talk (hold key) and Tap-to-Record (tap key) seamlessly on Linux.
* **Technical Design**:
  - Implement 50ms `RELEASE_GRACE` debounce to ignore Linux X11 synthetic key repeats.
  - If held > 300ms, release immediately stops recording. If released < 300ms, stays recording until tapped again.
* **Target Files**: `tray_app.py`, `engine.py`
* **Complexity**: Medium | **Impact**: High (ergonomics)

#### [TODO-D3] Background Eager Pre-Warm Daemon Thread
* **Objective**: Eliminate the 33-second first-audio delay on application startup.
* **Technical Design**:
  - On tray startup, spawn a low-priority daemon thread.
  - Passes 0.1s of silence through `transcribe_cpp` to compile Vulkan shaders.
  - Pings Ollama with a 1-token prompt with configured `OLLAMA_KEEP_ALIVE`.
  - When user presses hotkey, system is already hot and responds in < 0.5s.
* **Target Files**: `tray_app.py`, `engine.py`
* **Complexity**: Low | **Impact**: High (eliminates cold start)

---

### Track E: Dual-PC Portability & Self-Healing Doctor

#### [TODO-E1] Unified One-Click Diagnostic Tool (`doctor.py`)
* **Objective**: Instantly detect and report environment issues when running on Home PC (Ubuntu 26.04, Python 3.14, RTX 3060) vs Office PC (Ubuntu 22.04, Python 3.10, CPU).
* **Technical Design**:
  - Command: `python3 doctor.py`
  - Verifies:
    1. Python version & required modules.
    2. Vulkan / GPU acceleration vs CPU fallback.
    3. Audio capture (mic input test) & playback (chimes test).
    4. Ollama connectivity & installed models (`qwen2.5:3b`, etc.).
    5. Wayland vs X11 typing tool (`ydotool` daemon status / `xdotool`).
    6. Obsidian vault directory access.
* **Target Files**: `doctor.py` (new), `README.md`
* **Complexity**: Low-Medium | **Impact**: Very High (smooth cross-PC operation)

#### [TODO-E2] Unified Dependency Modernization (`pyproject.toml`)
* **Objective**: Merge split `requirements.txt` and `pyproject.toml` into a single, clean PEP 621 package with optional extras (`[gpu]`, `[review]`, `[audio-to-idea]`).
* **Target Files**: `pyproject.toml`, `requirements.txt`
* **Complexity**: Low | **Impact**: Medium (clean maintainability)

---

### Track F: Terminal & CLI Superpowers

#### [TODO-F1] Live Rich Terminal Dictation HUD (`pwd_cli.py`)
* **Objective**: A live terminal status HUD in `pwd_cli.py` showing live audio VU levels, active profile, and instantaneous transcription streaming directly into terminal.
* **Technical Design**:
  - Use `rich.live.Live` and `rich.panel.Panel`.
  - Dictate directly into clipboard or stdout pipe (`./pwd_cli.py --listen | grep ...`).
* **Target Files**: `pwd_cli.py`
* **Complexity**: Low-Medium | **Impact**: High for terminal users

#### [TODO-F2] Bash/Zsh Shell Direct Voice Typing Alias
* **Objective**: One shortcut to speak commands directly into the current terminal prompt.
* **Target Files**: `scripts/terminal_voice.sh`, `docs/setup_guide.md`
* **Complexity**: Low | **Impact**: Medium

---

## 5. Actionable Selection Matrix

Below is a quick overview of the most impactful TODO items ready for immediate execution:

| ID | Title | Domain | Effort | Impact | Key Benefit |
|:---:|---|:---:|:---:|:---:|---|
| **A1** | **Pre-Speech Ring Buffer** | Audio/VAD | 1-2 hrs | ⭐️⭐️⭐️⭐️⭐️ | Never cuts off the first spoken word |
| **B1** | **Floating Minimal Pill Overlay** | GUI/Visual | 2-3 hrs | ⭐️⭐️⭐️⭐️⭐️ | Sleek on-screen state widget (Idle ➔ Mic ➔ Brain ➔ Done) |
| **D1** | **Clipboard Save & Restore Auto-Paste** | Desktop | 1 hr | ⭐️⭐️⭐️⭐️⭐️ | Seamless paste without losing clipboard history |
| **D3** | **Background Pre-Warm Daemon** | Performance | 1 hr | ⭐️⭐️⭐️⭐️⭐️ | Eliminates 33s cold-start lag completely |
| **C1** | **Microsecond Filler Word Remover** | Text Engine | 1 hr | ⭐️⭐️⭐️⭐️ | Strips "um"/"uh"/"मतलब" in 0.1ms before LLM |
| **E1** | **Unified Environment Doctor (`doctor.py`)** | Portability | 1-2 hrs | ⭐️⭐️⭐️⭐️ | Self-healing check across Home & Office PCs |
| **F1** | **Rich Terminal Dictation HUD** | CLI/Terminal | 1-2 hrs | ⭐️⭐️⭐️⭐️ | Terminal-first live voice streaming dashboard |
