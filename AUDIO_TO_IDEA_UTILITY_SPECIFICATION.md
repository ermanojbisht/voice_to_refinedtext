# Technical Specification & Architecture Document: "AudioToIdea"
## Voice-to-Actionable-Intelligence Processing Utility

**Document Version:** 1.0.0  
**Target Architecture:** Cross-Platform (Linux, macOS, Windows)  
**Phased Delivery:** Phase 1 (Core Engine & CLI) | Phase 2 (Native Desktop / Modern GUI)

---

## 1. Executive Summary & Vision

### 1.1 Problem Statement
Field officers, engineers, and domain experts frequently record spontaneous voice notes during site inspections, review meetings, and brainstorming sessions. Converting these raw recordings into actionable work products currently suffers from four systemic failures:
1. **Truncation & Stalling in Standard ASR**: Off-the-shelf Whisper implementations stall or exit early when long pauses or ambient silence occur in spontaneous speech.
2. **Poor Field Audio Quality**: Unprocessed field recordings suffer from low input gain, wind noise, and vehicle vibrations.
3. **Loss of Technical Nuance**: Generic summarizers hallucinate or discard specialized administrative and regional terminology (e.g., *RoW*, *CALA*, *PARIVESH*, *Dakhil-Kharij*, *EDS*).
4. **Disconnection between Verbatim and Intent**: Users need both a verbatim, timestamped record for auditability **and** a distilled, structured synthesis of actionable ideas for executive escalation.

### 1.2 System Vision
**AudioToIdea** is an offline-first, domain-aware pipeline that ingests raw audio files or directories, optimizes acoustics for neural speech engines, runs chunked local ASR without early-exit defects, and leverages user-supplied domain context to produce structured action/idea documents alongside timestamped transcripts.

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             INPUT INGESTION LAYER                                │
│   Single Audio File (.mp3, .wav, .m4a, .ogg)  OR  Directory (Batch / Watch Mode) │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   ACOUSTIC NORMALIZATION & PREPROCESSING ENGINE                  │
│  - 16 kHz Mono Downsampling (PCM 16-bit) via FFmpeg                              │
│  - EBU R128 / Peak Loudness Normalization (-20 LUFS / -3 dBFS)                   │
│  - Adaptive Silence-Aware Windowing (60s chunks with 1.5s cross-fade)            │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      LOCAL ASR INFERENCE ENGINE (OFFLINE-FIRST)                  │
│  - Engine: faster-whisper (CTranslate2) or whisper.cpp                           │
│  - Hardware: Auto-detect NVIDIA CUDA (FP16), Apple Silicon (MPS), or CPU (INT8)  │
│  - Model Management: Local Hub / Cached Directory (large-v3-turbo / custom)     │
│  - Output: Verbatim Timestamped Segments [MM:SS]                                 │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
┌──────────────────────────────────────┐  ┌────────────────────────────────────────┐
│     VERBATIM TRANSCRIPT GENERATOR    │  │       CONTEXTUAL DISTILLATION ENGINE   │
│  - Output: [filename].txt            │  │  - Inputs: Verbatim + Domain Context   │
│  - Formats: Clean TXT, SRT, VTT, JSON│  │  - LLM Engine: Local Ollama / Qwen /   │
│  - Exact timestamps for auditing     │  │                Cloud API (Optional)    │
└──────────────────────────────────────┘  │  - Output: [filename]_idea.txt         │
                                          │  - Structured Policy / Action Extraction│
                                          └────────────────────────────────────────┘
```

---

## 3. Functional Requirements

### 3.1 Ingestion & File Handling
* **REQ-ING-1: Flexible Input Target**: The utility must accept either a single file path (`--input /path/to/note.mp3`) or a folder path (`--input /path/to/recordings/`).
* **REQ-ING-2: Format Agnostic**: Support input containers: `.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`, `.webm`.
* **REQ-ING-3: Idempotency & Skip Logic**: By default, the engine must skip audio files that already have matching `.txt` outputs, unless `--overwrite` is specified.
* **REQ-ING-4: Watcher Mode**: Ability to run in continuous background daemon mode (`--watch`), processing new recordings as soon as they are saved in a target folder.

### 3.2 Acoustic Enhancement & Audio Preparation
* **REQ-AUD-1: Native Resampling**: Automatically re-sample all audio to single-channel (mono) 16,000 Hz, 16-bit Linear PCM, matching Whisper's internal receptive field.
* **REQ-AUD-2: Loudness Normalization**: Normalize fluctuating volume to `-20 LUFS` (with a `-2.0 dB` true-peak ceiling) to equalize distant speaking and soft dictations.
* **REQ-AUD-3: Chunk-Based Segmentation**: To prevent the known CTranslate2 / Whisper bug where long pauses (>10s) trigger premature loop termination, audio must be processed in fixed 60–90 second chunks with an overlapping boundary (1.5 seconds) and automatic deduplication of border tokens.

### 3.3 ASR Engine & Model Management
* **REQ-ASR-1: Offline-First Priority**: The system must run completely offline without external internet calls by default.
* **REQ-ASR-2: Configurable Model Location**:
  * Default fallback to standard local model hubs (e.g., local HuggingFace cache or dedicated model directory).
  * Manageable via CLI flag (`--model /path/to/weights`), config file (`config.yaml`), or environment variable (`ASR_MODEL_PATH`).
* **REQ-ASR-3: Hardware Acceleration**:
  * NVIDIA GPU: `device="cuda"`, `compute_type="float16"`.
  * CPU Fallback: `device="cpu"`, `compute_type="int8"` with multi-threading.
* **REQ-ASR-4: Code-Switching & Multilingual Support**: Retain mixed-language capability (e.g., English-Hindi Hinglish) without phoneme corruption.

### 3.4 Domain Context & Idea Extraction
* **REQ-CTX-1: Context Injection**: The user can provide high-level domain context via a string (`--context "..."`) or a file (`--context-file context.md`).
* **REQ-CTX-2: Structured Extraction**: When summary generation is active, the engine must produce `*_idea.txt` structured strictly into:
  1. *Core Operational Bottlenecks / Observations*
  2. *Actionable Proposals / Solutions*
  3. *Institutional / Regulatory Implications*
* **REQ-CTX-3: Modular Summarizer Backend**:
  * *Option A (Default Local)*: Local small LLM via Ollama or llama-cpp-python (e.g., `qwen2.5:7b-instruct-q4_K_M` or `phi-3-mini`).
  * *Option B (Cloud API)*: Configurable endpoint for OpenAI/Gemini/Anthropic with user API key.
  * *Option C (Rule-Based Fallback)*: Keyword and agenda-matching template when no LLM is configured.

---

## 4. Phase 1: Command-Line Interface (CLI) Specification

### 4.1 CLI Syntax & Commands

```bash
# Basic file transcription
audio2idea transcribe --input /path/to/recording.mp3

# Batch folder processing with domain context and summary generation
audio2idea process --input ./field_recordings/ \
                   --context "Uttarakhand hill roads, forest clearances, land acquisition" \
                   --model /media/manoj/F1/huggingface_cache/hub/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/... \
                   --output-dir ./processed_notes/

# Watcher mode: continuously process incoming phone recordings
audio2idea watch --input ~/VoiceRecorder/ --context-file ./project_context.txt
```

### 4.2 Parameter Matrix

| Flag | Short | Default | Description |
| :--- | :---: | :---: | :--- |
| `--input` | `-i` | *(Required)* | File or directory path to process |
| `--output-dir` | `-o` | Same as input | Destination directory for output files |
| `--context` | `-c` | `None` | Inline domain context string |
| `--context-file`| `-cf`| `None` | Path to text file containing background context |
| `--model` | `-m` | Cached path | Path to local faster-whisper / llamafile model |
| `--device` | `-d` | `auto` | Execution device: `cuda`, `cpu`, `mps`, or `auto` |
| `--no-summary` | | `False` | Skip `*_idea.txt` generation; produce only transcript |
| `--format` | `-f` | `txt` | Transcript format: `txt`, `srt`, `vtt`, `json` |
| `--chunk-size` | | `60` | Audio chunk size in seconds for safe processing |
| `--overwrite` | | `False` | Force re-transcription of previously processed files |
| `--watch` | `-w` | `False` | Run as a folder-monitoring daemon |

### 4.3 Output File Conventions
For an input audio file `Standard recording 34.mp3`:
* `Standard recording 34.txt`: Exact timestamped transcript (`[01:24] Spoken sentence...`).
* `Standard recording 34_idea.txt`: Contextual structured idea document (Markdown/TXT).
* `Standard recording 34.meta.json`: (Optional) Processing metadata (duration, processing time, detected language, confidence).

---

## 5. Phase 2: Graphical User Interface (GUI) Specification

### 5.1 Recommended Architecture & Tech Stack
* **Framework**: **PySide6 (Qt for Python)** for native desktop performance on Linux/Windows/Mac, or **Tauri + Svelte/Vue** for a lightweight modern web-tech desktop wrapper.
* **Audio Visualizer**: Native waveform renderer using `pyqtgraph` or Web Audio API.

### 5.2 Core GUI Screens & Modules

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ AudioToIdea - Executive Voice Intelligence Hub                      [ _ ][ 口 ][ X ]│
├──────────────────────┬───────────────────────────────────────────────────────────┤
│ 📁 BATCH QUEUE       │ 🎙️ AUDIO WORKBENCH: Standard recording 34.mp3             │
│                      ├───────────────────────────────────────────────────────────┤
│ [➕ Add Files/Folder] │ [▶ Play] [⏸] 02:14 / 08:34  ═══════●══════════════ [1.2x] │
│                      │                                                           │
│ ☑ rec_34.mp3 [Done]  │ 📝 VERBATIM TRANSCRIPT             💡 SYNTHESIZED IDEAS   │
│ ☑ rec_35.mp3 [Done]  │ ┌───────────────────────────────┐ ┌─────────────────────┐ │
│ ⏳ rec_36.mp3 [78%]   │ │[00:00] solving issues like... │ │### 1. Tier-Based... │ │
│ ⏳ rec_37.mp3 [Queue] │ │[00:08] projects some are...   │ │- Project review...  │ │
│                      │ │[00:16] bridge hardly 0.1 ha...│ │- Brownfield vs...   │ │
│                      │ │[01:14] NH needs widening...   │ │                     │ │
│                      │ └───────────────────────────────┘ └─────────────────────┘ │
├──────────────────────┴───────────────────────────────────────────────────────────┤
│ ⚙️ CONTEXT & SETTINGS:                                                            │
│ Context Profile: [Uttarakhand Linear Infrastructure ▼]  [✏️ Edit Context]         │
│ Model: Large-V3-Turbo (GPU Active: RTX 3060 - 11.6GB Free)      [ Export Word/PDF ]│
└──────────────────────────────────────────────────────────────────────────────────┘
```

#### Key GUI Capabilities:
1. **Interactive Audio-Text Synchronization**: Clicking on any sentence in the transcript seeks the audio player to that exact second.
2. **Context Profile Switcher**: Dropdown to switch between project profiles (e.g., "Uttarakhand Linear Infra", "Budget Review", "Disaster Assessment"), automatically reloading the relevant domain glossary.
3. **Split-Screen Editor**:
   * Left: Verbatim transcript with inline editing.
   * Right: Markdown-rendered idea summary with instant export to PDF, Word (`.docx`), or Markdown (`.md`).
4. **Hardware Monitor Bar**: Real-time VRAM/GPU status display so the user knows model readiness and memory utilization.

---

## 6. Data Schemas & Formats

### 6.1 Configuration Schema (`config.yaml`)
```yaml
version: "1.0"
models:
  default_asr: "/media/manoj/F1/huggingface_cache/hub/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/snapshots/0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf"
  device: "cuda"
  compute_type: "float16"
  chunk_duration_sec: 60
  overlap_sec: 1.5

summarizer:
  engine: "ollama"           # Options: "ollama", "gemini", "openai", "rule-based"
  model: "qwen2.5:7b-instruct"
  endpoint: "http://localhost:11434"
  temperature: 0.2

audio_processing:
  sample_rate: 16000
  normalize_lufs: -20.0
  remove_silence: false     # Handled via chunking rather than hard stripping

output:
  save_transcript: true
  save_idea: true
  save_metadata_json: false
  formats: ["txt", "idea.txt"]
```

### 6.2 Output Idea Template (`*_idea.txt`)
```markdown
# EXECUTIVE BRIEF & ACTIONABLE SYNTHESIS
**Source Audio:** [filename.mp3] | **Duration:** [MM:SS] | **Date:** [YYYY-MM-DD]
**Context Applied:** [Context Title / Profile]

---

### 1. Core Bottlenecks & Operational Realities
* [Clear statement of the obstacle identified from the audio]
* [Specific ground friction / administrative deadlocks described]

### 2. Concrete Proposals & Reforms
* [Operational solution proposed by speaker]
* [Procedural, contractual, or technical adjustments]

### 3. Institutional & Policy Implications
* [Jurisdiction: Central Ministry ask vs. State Government order]
* [Departmental responsibilities and oversight structure]
```

---

## 7. Implementation Roadmap for the Standalone Project

| Milestone | Deliverables | Target Timeline |
| :--- | :--- | :--- |
| **M1: Audio Pre-Processor** | FFmpeg-based audio converter; 16kHz mono normalization; 60s chunking generator with boundary handling. | Week 1 |
| **M2: ASR Pipeline** | `faster-whisper` integration; CUDA/CPU hardware auto-detector; batch & directory traversal; `.txt` formatter. | Week 2 |
| **M3: Contextual Distiller** | Prompt template system; local Ollama / cloud API bridge; structured `*_idea.txt` synthesizer. | Week 3 |
| **M4: CLI Packaging** | Command-line interface with `argparse`/`click`; watcher mode; packaging as pip-installable binary / package. | Week 4 |
| **M5: Desktop GUI** | PySide6 UI; audio player with karaoke-style text sync; context selector; batch progress queue. | Weeks 5–6 |

---

*This specification document is preserved in the repository as a blueprint for launching the standalone project.*
