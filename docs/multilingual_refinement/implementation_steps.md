# Multilingual Refinement & Code-Switching — Implementation Steps

## Phase 1: Planning & Live Documentation
- [x] Create `docs/multilingual_refinement/plan.md`
- [x] Create `docs/multilingual_refinement/implementation_steps.md`
- [x] Create `docs/multilingual_refinement/progress_tracker.md`

## Phase 2: Prompt Templates Creation
- [x] Create `prompts/default/bilingual.txt` (Default: preserves mixed speech, English in Latin script, Hindi in Devanagari, cleans stutters/fillers, fixes PWD acronyms)
- [x] Create `prompts/default/pure_english.txt` (Translates Hindi/mixed to polished English, refines English)
- [x] Create `prompts/default/pure_hindi.txt` (Structures in formal Devanagari Hindi, preserves technical terms in Latin English)
- [x] Create `prompts/default/roman_hinglish.txt` (100% Latin alphabet conversational Hinglish)

## Phase 3: Configuration Schema & Defaults
- [x] Update `config.json` with `"LANGUAGE_MODE": "bilingual"`
- [x] Update `utils.load_config()` to include `"LANGUAGE_MODE": "bilingual"` default
- [x] Map legacy `MODE: "translate"` $\rightarrow$ `pure_english` for 100% backward compatibility

## Phase 4: ASR Bilingual Steering & Whisper Devanagari Trap Fix (`engine.py`)
- [x] Remove rigid Devanagari-only prompt (`_HINDI_PROMPT = "नमस्ते, यह हिंदी में है।"`)
- [x] Add `_BILINGUAL_PROMPT = "PWD civil works, road and bridge inspection, EE, AE, JE, NIT, MB, RCC, निविदा, सड़क निर्माण।"`
- [x] In `pure_english` mode, constrain Whisper to `language="en"`
- [x] In `bilingual` mode, allow natural code-switching via `_BILINGUAL_PROMPT`
- [x] Fix `_HINDI_FAMILY` re-transcription to guard against false-positive English classification

## Phase 5: LLM Refinement Routing (`engine.py` & `utils.py`)
- [x] Update `engine.py:refine()` to resolve `LANGUAGE_MODE` and route to the appropriate prompt template
- [x] Ensure backward compatibility with `refine(text, mode="translate")`
- [x] Ensure PWD terminology normalization runs on all mode outputs

## Phase 6: System Tray & GUI Integration (`tray_app.py`, `config_gui.py`, `main_gui.py`)
- [x] Add 1-click Language Mode cycling to `tray_app.py` menu
- [x] Add Language Mode dropdown with descriptive tooltips to `config_gui.py` Voice Refiner tab
- [x] Update `main_gui.py` status badges to reflect active Language Mode

## Phase 7: Verification & Unit Tests
- [x] Authored `tests/test_multilingual_refinement.py` covering all 4 modes and legacy fallback
- [x] Run test suite (`pytest tests/test_multilingual_refinement.py`)
- [x] Run full project test suite (`pytest`) to confirm zero regressions
