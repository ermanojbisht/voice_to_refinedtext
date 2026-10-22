# AI Voice Refiner — Documentation Portal

Welcome to the centralized documentation portal for **Voice-to-RefinedText**. This documentation is divided into clearly styled sections for **End Users** and **Core Developers / Contributors**.

---

## 👤 User-Level Documentation (Daily Operation)

Designed for writers, engineers, and everyday users who want fast, reliable voice dictation, Markdown narration, and evening reviews.

| Document | Purpose & Key Topics |
| :--- | :--- |
| **[Office PC Setup Guide](OFFICE_PC_SETUP_GUIDE.md)** | **Workstation Deployment**: Complete offline setup guide for office PC, USB pen drive asset checklist, model paths, autostart, and daily PWD engineering workflows. |
| **[User Guide](USER_GUIDE.md)** | **Master User Manual**: 1-letter terminal workflow (`v`), global hotkeys (`Ctrl+Space`), Walkie-Talkie push-to-talk, safe clipboard auto-paste, and troubleshooting with `v-doc`. |
| **[Configuration Guide](CONFIGURATION_GUIDE.md)** | **Single Source of Truth**: The complete 9-chapter reference compiled directly into the standalone HTML manual. All JSON settings, ASR presets, and GUI options. |
| **[Speech Synthesis & Voice Guide](SPEECH_SYNTHESIS_AND_VOICE_GUIDE.md)** | **Indian TTS Guide**: Voice selection (`en_in_female`, `en_in_male`, `hf_alpha`, `hm_omega`), reading Obsidian notes with `v-read`, and discovering community Kokoro voices. |
| **[Evening Review Studio Guide](EVENING_REVIEW_EXECUTIVE_STUDIO_GUIDE.md)** | **Daily Note Journaling**: Step-by-step evening debrief with Obsidian, voice prompts, wellness logs, and automatic 7-day task carry-forward. |
| **[Hotkey & Walkie-Talkie Guide](HOTKEY_AND_WALKIE_TALKIE_GUIDE.md)** | **Hardware Key Listener**: Evdev kernel-level hotkey configuration, hold-vs-toggle thresholds, and Wayland vs X11 paste mechanics. |
| **[Offline HTML Manual](generated/manual.html)** | **Complete Standalone Manual**: Beautifully styled Catppuccin dark-theme manual for offline viewing and distribution. |

---

## 🛠️ Developer & Architecture Documentation (Internals)

Designed for AI engineers, systems programmers, and contributors working on the core audio pipeline, LLMs, and packaging.

| Document | Architectural Domain |
| :--- | :--- |
| **[Developer Guide](DEVELOPER_GUIDE.md)** | **Master Architecture Manual**: Full pipeline blueprint, VAD ring buffer, multi-engine ASR factory, LLM prompt engineering, and secrets resolution. |
| **[Pause-Guided Chunking Philosophy](PAUSE_GUIDED_CHUNKING_PHILOSOPHY.md)** | **Audio Pipeline**: Non-destructive audio slicing using natural silence gaps (25–35s windows) to prevent word-clipping during long recordings. |
| **[Universal Speech Synthesis Specification](CONCEPT_UNIVERSAL_SPEECH_SYNTHESIS.md)** | **TTS Core Architecture**: Text normalizer pipeline, voice embedding interpolation math ($0.80 \cdot \mathbf{v}_{\text{hi}} + 0.20 \cdot \mathbf{v}_{\text{gb}}$), and process concurrency. |
| **[Fuzzy N-Gram Domain Dictionary](CONCEPT_FUZZY_NGRAM_DOMAIN_DICTIONARY.md)** | **Vocabulary Correction**: Sliding $N$-grams ($1..4$), Levenshtein edit distance with Soundex phonetic match boost (0.3x), and length-difference guards. |
| **[Terminal Dictation HUD Concept](CONCEPT_TERMINAL_DICTATION_HUD.md)** | **CLI Architecture**: Rich terminal animated VU volume meter, VAD status transitions, and pipe-safe TTY separation (HUD to `stderr`, clean text to `stdout`). |
| **[Unified Dependency Modernization](CONCEPT_UNIFIED_DEPENDENCY_MODERNIZATION.md)** | **Cross-Version Packaging**: Modern PEP 621 `pyproject.toml` configuration supporting Ubuntu 22.04 (Python 3.10) through Ubuntu 26.04 (Python 3.14). |
| **[Benchmark Evaluation Guide](BENCHMARK_EVALUATION_GUIDE.md)** | **Quality & Latency Testing**: Automated benchmarking methodology for Word Error Rate (WER), Time-to-First-Token (TTFT), and VRAM utilization. |
| **[Manual Maintenance Guide](MANUAL_AUTHORING_AND_MAINTENANCE_GUIDE.md)** | **Documentation Pipeline**: Single-source-of-truth compilation rules for `ManualService` and live-sync tests. |

---

## 🏛️ Domain Integration: PWD Uttarakhand

Specialized tools for bilingual civil engineering workflows, public works terminology, and technical tender documents.

| Tool / Service | Capabilities |
| :--- | :--- |
| **CLI Terminology Lookup (`pwd_cli.py`)** | Fast abbreviation searches (`EE`, `NIT`, `MB`, `DPR`) with English definitions and Hindi official designations. |
| **Fuzzy Translation Engine (`pwd_helper/`)** | Offline dictionary correction combined with online Google Translation fallback for complex engineering phrases. |
| **FastAPI Microservice (`pwd_helper/api.py`)** | REST endpoints (`/api/translate`, `/api/abbreviation`) for external integration with office portals and Laravel dashboards. |

---

## 📚 Historical Archives & Research (`docs/archive/`)

Preserved design documents, legacy specifications, and benchmark research logs:
- `docs/archive/indian_speech_synthesis_research.md`: In-depth 2026 research into Indian speech synthesis paradigms (IndicF5, Orpheus-3B, Kokoro-82M, Sarvam).
- `docs/archive/early_idea_draft.md`: Original prototype vision.
- `docs/archive/legacy_setup_guide.md`: Historical shell setup scripts.
- `docs/archive/GEMINI_legacy_spec.md`: Initial system requirements specification.
