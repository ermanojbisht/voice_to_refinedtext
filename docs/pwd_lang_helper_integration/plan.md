# PWD Language Helper Integration & Hybrid System — Architecture Plan

**Created:** 2026-10-19  
**Status:** In Review / Ready for Implementation  
**Source Origin:** `/home/manoj/my_lang_helper`  
**Target Project:** `/media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext`  
**Target Environments:**
- Home PC: Ubuntu 26.04 LTS, Python 3.14, NVIDIA GeForce RTX 3060 12GB
- Office PC: Ubuntu 22.04 LTS, Python 3.10, Low-VRAM / Shared GPU / CPU

---

## 1. Executive Summary & Objective

In PWD (Public Works Department) Uttarakhand, engineering officers and staff routinely handle specialized terminology, abbreviations, and bilingual communications (English ⇄ Hindi). 

The standalone `/home/manoj/my_lang_helper` project successfully solved basic lookup and translation via a terminal CLI and FastAPI backend. However, because it operated in isolation, it could not benefit from:
1. **Real-time voice dictation & speech recognition** (Whisper / Nemotron).
2. **Context-aware local LLM refinement** (Ollama `qwen2.5:3b`, `aya-expanse`).
3. **Desktop tray accessibility, global hotkeys, and Obsidian daily review workflows**.

Conversely, `voice_to_refinedtext` previously lacked explicit domain knowledge of PWD abbreviations (often transcribing `"NIT"` as `"nit"` or `"night"`, `"MB"` as `"mb"`, or `"EE"` as lowercase letters), and required a full LLM invocation even for simple one-word terminology lookups.

**The Goal**: Merge `/home/manoj/my_lang_helper` into `voice_to_refinedtext` as a first-class, optimized subsystem featuring a **hybrid architecture** (enhanced CLI + GUI cards + speech post-corrector + FastAPI endpoint for Laravel).

---

## 2. Technical Architecture & System Design

```
                                  ┌──────────────────────────────────────────────────┐
                                  │           pwd_dict.json (PWD Dictionary)         │
                                  │   45+ Officers, Documents, Schemes, Technical    │
                                  └─────────────────────────┬────────────────────────┘
                                                            │
                                  ┌─────────────────────────▼────────────────────────┐
                                  │               pwd_helper/ Engine                 │
                                  │  • core.py (Lookup & Search)                     │
                                  │  • normalizer.py (ASR Speech Casing & Correction)│
                                  │  • translator.py (Argos Offline + Ollama + Web)  │
                                  └─────────────────────────┬────────────────────────┘
                                                            │
         ┌──────────────────────────────────────────────────┼──────────────────────────────────────────────────┐
         ▼                                                  ▼                                                  ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐               ┌──────────────────────────────┐
│       Hybrid CLI             │              │       GUI Integration        │               │       External API           │
│      (`pwd_cli.py`)          │              │ (`main_gui.py` & `tray_app`) │               │     (`pwd_helper/api.py`)    │
├──────────────────────────────┤              ├──────────────────────────────┤               ├──────────────────────────────┤
│ • Interactive REPL prompt    │              │ • "📚 PWD Glossary" card     │               │ • FastAPI server (port 8000) │
│ • Voice input toggle ('v')   │              │ • Live instant search box    │               │ • Laravel web app HTTP call  │
│ • One-shot terminal commands │              │ • Tray menu quick-lookup     │               │ • REST: /api/translate       │
│ • Clipboard auto-copy (-c)   │              │ • In-speech term correction  │               │ • REST: /api/abbreviation    │
└──────────────────────────────┘              └──────────────────────────────┘               └──────────────────────────────┘
```

---

## 3. Subsystem Detailed Specifications

### 3.1 Core Module: `pwd_helper/`
Located at `voice_to_refinedtext/pwd_helper/`:
1. **`pwd_dict.json`**:
   - Curated dictionary containing:
     - `officers`: E-IN-C, CE, SE, EE, AE, JE, HOD, SDO, XEN
     - `documents`: SOR, MB, NIT, AS, TS, RA BILL, FINAL BILL, HR, BOQ, DPR, EOI, LOI, WO, CC, NOC, UC
     - `schemes`: PMGSY, NHAI, ADB, NABARD, RIDF, PMC, CRF, SCSP, TSP, SIDCUL
     - `technical`: RCC, PCC, WBM, GSB, DBM, BC, SDBC, MSS, PC, TC, EMD, SD, BM, RL, RW, ROW, CD, LSCD
   - Supports user-defined extensions in `pwd_custom_dict.json` (so users can add division-specific codes without modifying source files).

2. **`core.py`**:
   - `lookup_abbreviation(text)`: O(1) case-insensitive exact match.
   - `search_abbreviations(query)`: Substring match across abbreviations, English expansions, and Hindi meanings.
   - `list_abbreviations()`: Grouped by category.
   - `add_custom_abbreviation(abbr, meaning, category)`: Safe JSON persistence.

3. **`normalizer.py` (ASR Speech Post-Corrector)**:
   - Operates on raw transcripts from `engine.py` (Whisper / Nemotron).
   - Word boundary regex replacement ensuring accurate casing (e.g. `\b(ee|e\.e\.)\b` ➔ `EE`, `\brcc\b` ➔ `RCC`, `\bnit\b` ➔ `NIT`, `\bmb\b` ➔ `MB`).
   - Runs in `< 1ms` on CPU without any deep learning overhead.

4. **`translator.py` (Tri-Tier Hybrid Translation)**:
   - **Tier 1 (Instant Offline)**: `argostranslate` (CTranslate2, ~200MB model). Latency `< 50ms`, zero GPU VRAM consumption.
   - **Tier 2 (Context-Aware LLM)**: Local Ollama (`qwen2.5:3b`, `aya-expanse`) for paragraphs and nuanced phrasing.
   - **Tier 3 (Online Fallback)**: `deep-translator` (Google Translate) when internet is reachable.

---

### 3.2 Advanced Hybrid CLI: `pwd_cli.py`
A high-productivity CLI for developers and terminal users:
- **One-Shot Execution**:
  ```bash
  python3 pwd_cli.py ee                 # -> Executive Engineer (अधिशासी अभियंता)
  python3 pwd_cli.py search road        # -> Lists WBM, GSB, DBM, BC, SDBC
  python3 pwd_cli.py translate "Bridge" # -> पुल (offline)
  python3 pwd_cli.py nit -c             # -> Copies expansion to clipboard
  ```
- **Interactive REPL**:
  - `[auto] >> EE`: instant lookup.
  - `[auto] >> v`: **Voice input mode**! Records from microphone for 3 seconds (or until silence), transcribes via Whisper/Nemotron, and outputs translation/abbreviation directly to terminal and clipboard.
  - Commands: `list`, `search <term>`, `mode <offline|online|auto>`, `add <abbr>=<meaning>`, `exit`.

---

### 3.3 GUI Integration: `main_gui.py` & `tray_app.py`
1. **Main GUI (`main_gui.py`)**:
   - Add a collapsible or dedicated **"📚 PWD Uttarakhand Glossary" Card**:
     - Live search entry box. As you type, matching abbreviations appear instantly with their category badge, full English designation, and Hindi translation.
     - "📋 Copy" button per search result for 1-click clipboard insertion.
2. **System Tray (`tray_app.py`)**:
   - Add tray menu action: `"📚 PWD Terminology Lookup"`.
   - Opens a fast, lightweight modal search dialog (Spotlight-style) allowing the user to search any PWD abbreviation from any desktop workspace without opening terminal.

---

### 3.4 Web Integration: FastAPI Server (`pwd_helper/api.py`)
- Retains full compatibility with Laravel web applications:
  - `GET /api/translate?text=...&mode=auto`
  - `GET /api/abbreviation?q=EE`
  - `GET /api/search?q=...`
  - `GET /api/abbreviations`
- Can be launched via `python3 -m pwd_helper api` or as a background service.

---

## 4. Performance & Compatibility Guarantees

1. **Zero Cold-Start Overhead**:
   - Dictionary lookup executes in memory in `< 0.05ms`.
   - Normalizer regex executes on full transcripts in `< 1.0ms`.
2. **VRAM Neutrality**:
   - The PWD glossary and Argos translation run entirely in CPU system RAM (~25MB resident), leaving 100% of GPU VRAM for Ollama and Whisper/Nemotron.
3. **Cross-Version Support**:
   - Python 3.10 (Ubuntu 22.04 Office PC) through Python 3.14 (Ubuntu 26.04 Home PC).
   - Strict typing compatibility: `typing.Union`, `typing.Optional`, no Python 3.10+ incompatible syntax.
