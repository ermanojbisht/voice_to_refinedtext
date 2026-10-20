# Implementation Steps: PWD Language Helper Integration & Hybrid System

**Plan Reference:** [docs/pwd_lang_helper_integration/plan.md](plan.md)  
**Tracker Reference:** [docs/pwd_lang_helper_integration/progress_tracker.md](progress_tracker.md)

---

## Phase 1: Core Engine & Dictionary Import
- [ ] **Step 1.1**: Create `pwd_helper/` package in `voice_to_refinedtext`:
  - `pwd_helper/__init__.py`: Package exports.
  - `pwd_helper/pwd_dict.json`: Copy curated dictionary with 45+ PWD Uttarakhand terms.
  - `pwd_helper/core.py`: Abbreviation lookup, category grouping, fuzzy/substring search, custom dictionary persistence (`pwd_custom_dict.json`).
- [ ] **Step 1.2**: Implement `pwd_helper/normalizer.py`:
  - Regex-based term and casing corrector for Whisper / Nemotron transcripts.
  - Test suite covering case-normalization of `"ee"`, `"nit"`, `"mb"`, `"rcc"`, `"sor"`, `"boq"`.
- [ ] **Step 1.3**: Implement `pwd_helper/translator.py`:
  - Tri-tier translation strategy (Argos CTranslate2 offline, Ollama LLM, Google Translate online fallback).
  - Graceful fallback if `argostranslate` or `deep-translator` packages are not installed.

---

## Phase 2: Speech Engine Integration (`engine.py`)
- [ ] **Step 2.1**: Hook `pwd_helper.normalizer` into `VoiceEngine.transcribe()` in `engine.py`:
  - Automatically correct and capitalize PWD terms before LLM refinement.
- [ ] **Step 2.2**: Update system prompt builder in `utils.py` to optionally inject active PWD terms into Ollama context.
- [ ] **Step 2.3**: Verify existing pipeline tests pass without regressions.

---

## Phase 3: Advanced Hybrid CLI (`pwd_cli.py`)
- [ ] **Step 3.1**: Create `pwd_cli.py`:
  - Support one-shot terminal lookups: `python3 pwd_cli.py <query>` (e.g. `ee`, `nit`, `search bridge`, `translate "..."`).
  - Support clipboard flag `-c` / `--copy`.
- [ ] **Step 3.2**: Add interactive REPL with commands:
  - `list`, `search <term>`, `mode <offline|online|auto>`, `add <abbr>=<meaning>`, `exit`.
  - Press `v` (or command `voice`) to trigger instant microphone recording, transcribe speech, and display PWD lookup / translation.

---

## Phase 4: GUI & System Tray Integration
- [ ] **Step 4.1**: In `main_gui.py`:
  - Add a collapsible or dedicated **"📚 PWD Uttarakhand Glossary" Card**:
    - Live search entry box with instant filtering.
    - Displays category badge, full English designation, and Hindi translation.
    - 1-click copy button per result.
- [ ] **Step 4.2**: In `tray_app.py`:
  - Add `"📚 PWD Terminology Lookup"` menu action opening a fast spotlight search dialog.
- [ ] **Step 4.3**: In `config_gui.py`:
  - Add toggle in Features tab: `pwd_terminology_corrector` (enabled by default).

---

## Phase 5: FastAPI Service & Laravel Integration
- [ ] **Step 5.1**: Implement `pwd_helper/api.py`:
  - FastAPI endpoints matching original `my_lang_helper/api.py` contracts:
    - `GET /api/translate`
    - `POST /api/translate`
    - `GET /api/abbreviation`
    - `GET /api/abbreviations`
    - `GET /api/search`
- [ ] **Step 5.2**: Add command launcher `python3 -m pwd_helper api` (or `--port 8000`).

---

## Phase 6: Verification, Unit Tests & Documentation
- [ ] **Step 6.1**: Create unit test suite in `tests/test_pwd_helper.py`:
  - Test exact lookup, case-insensitive match, partial search, normalizer on sample sentences, and API endpoint contracts.
- [ ] **Step 6.2**: Run full pytest test suite (ensure zero regressions across all 105 tests).
- [ ] **Step 6.3**: Update `README.md` and `docs/CONFIGURATION_GUIDE.md` with PWD helper features.
