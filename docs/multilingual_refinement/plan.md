# Multilingual Refinement & Code-Switching Architecture Plan

## 1. Executive Summary & Purpose

This document outlines the architecture for high-accuracy multilingual speech handling in **AI Voice Refiner**. It solves the acoustic false-positive trap where English speech was transliterated into Devanagari script (`"ना आई फाउंड ए प्रॉब्लम..."`), and establishes **4 distinct, intentional output modes** for bilingual Hindi-English workflows.

---

## 2. Core Problem & Root Causes Identified

1. **Acoustic False Positive in Whisper**:
   When speaking English with an Indian accent or ambient background noise, Whisper (`large-v3` / `large-v3-turbo`) unconstrained (`language=None`) frequently misclassifies audio as `"hi"` or `"ur"` with marginal confidence (~51%).
2. **Aggressive Devanagari Forcing**:
   `engine.py` formerly re-transcribed any audio in `_HINDI_FAMILY` with `language="hi"` and `initial_prompt="नमस्ते, यह हिंदी में है।"`. This compelled Whisper to decode English phonemes into Devanagari script.
3. **Downstream Script Classification Cascade**:
   `utils.detect_lang(text)` saw Devanagari characters, classified the text as `"hi"`, and routed it to `llama3-hindi` with a prompt commanding *"Devanagari output only, no translation"*.
4. **Lack of Language Intent**:
   The user had no mechanism to tell the system whether they wanted:
   - English kept in English,
   - Natural mixed Hinglish preserved, or
   - Translation into formal English or formal Hindi.

---

## 3. The 4 Language & Output Modes

```
                               ┌──────────────────────────────────────────────┐
                               │             Spoken Audio Input               │
                               │  Pure English / Pure Hindi / Mixed Hinglish  │
                               └──────────────────────┬───────────────────────┘
                                                      │
         ┌────────────────────────────┬───────────────┴───────────────┬────────────────────────────┐
         ▼                            ▼                               ▼                            ▼
┌──────────────────┐        ┌──────────────────┐            ┌──────────────────┐         ┌──────────────────┐
│  1. Bilingual    │        │ 2. Pure English  │            │  3. Pure Hindi   │         │4. Roman Hinglish │
│    (Default)     │        │ (Translation)    │            │ (Tech EN Intact) │         │ (Latin Alphabet) │
├──────────────────┤        ├──────────────────┤            ├──────────────────┤         ├──────────────────┤
│• Mirror spoken   │        │• Translates all  │            │• Formal Hindi    │         │• 100% Roman/Latin│
│  language mix    │        │  Hindi to English│            │  structure       │         │  alphabet script │
│• English in EN   │        │• Refines English │            │• Technical terms │         │• Natural spoken  │
│• Hindi in Deva   │        │• Formal corporate│            │  stay in English │         │  conversational  │
│• Refines grammar │        │  documentation   │            │• No silly forced │         │  Hinglish flow   │
│• Strips fillers  │        │  writing style   │            │  translations    │         │• Chat/Slack ready│
└──────────────────┘        └──────────────────┘            └──────────────────┘         └──────────────────┘
```

### Mode 1: `bilingual` (Default: Mirror What Was Spoken, Refined)
* **Goal**: Preserves the natural code-switching of bilingual speakers.
* **Whisper Steering**: Bilingual prompt (`"PWD civil works, road and bridge inspection, EE, AE, JE, NIT, MB, RCC, निविदा, सड़क निर्माण।"`).
* **Ollama Refinement (`bilingual.txt`)**:
  - Spoken English words & technical acronyms remain in English (`A-Z`).
  - Spoken Hindi words remain in Devanagari (`अ-ह`).
  - Stutters and filler words (*"um"*, *"uh"*, *"मतलब"*, *"जैसे कि"*) are removed.
  - PWD acronyms are properly capitalized (`EE`, `MB`, `NIT`, `RCC`).

### Mode 2: `pure_english` (Full Professional English)
* **Goal**: Delivers a single, polished, corporate/documentation-grade English paragraph regardless of input language.
* **Whisper Steering**: In pure English mode, Whisper is constrained to `language="en"`.
* **Ollama Refinement (`pure_english.txt`)**:
  - Translates Hindi and mixed Hinglish thoughts into fluent, idiomatic English.
  - Polishes vocabulary and punctuation.
  - Retains and capitalizes technical abbreviations.

### Mode 3: `pure_hindi` (Formal Hindi, Technical Terms in EN)
* **Goal**: Delivers official, formal Hindi (राजभाषा शैली) while keeping standard technical terms in clean English Latin script.
* **Whisper Steering**: Bilingual/Hindi steering.
* **Ollama Refinement (`pure_hindi.txt`)**:
  - Sentence structure, verbs, and postpositions are in formal Hindi (Devanagari).
  - Technical terms, acronyms, and modern tools (`EE`, `NIT`, `RCC Bridge`, `Server`, `Status`, `Online`) stay in English Latin letters.
  - Prevents artificial, archaic translations (e.g., does not replace "computer" with "संगणक").

### Mode 4: `roman_hinglish` (Conversational Latin Script Everywhere)
* **Goal**: Outputs conversational Hindi-English in 100% Latin/Roman alphabet for WhatsApp, Slack, ChatGPT, or rapid notes.
* **Ollama Refinement (`roman_hinglish.txt`)**:
  - Outputs purely in Latin characters (`"Aaj humne site visit kiya aur EE ne NIT issue karne ko bola."`).

---

## 4. Configuration Schema & Backward Compatibility

### Settings Key in `config.json`
```json
{
  "LANGUAGE_MODE": "bilingual",
  "MODE": "refine"
}
```
* **Valid Values**: `"bilingual"`, `"pure_english"`, `"pure_hindi"`, `"roman_hinglish"`.
* **Backward Compatibility**:
  - If a script or test calls `refine(text, mode="translate")`, it maps to `pure_english`.
  - If `LANGUAGE_MODE` is not present, it defaults to `"bilingual"`.
  - Existing `OLLAMA_MODELS` and `OLLAMA_TRANSLATE_MODELS` are respected.

---

## 5. Subsystem Isolation & Verification

1. **Evening Review**: Accumulates `raw_text` from `transcribe()` and uses its own step prompts in `review_config.json`. Improved transcription quality directly enhances Obsidian notes.
2. **Audio to Ideas**: Uses its own `audio_to_idea_config.json` and `synthesis.py` prompts. Zero regression.
3. **PWD Helper**: PWD normalizer integrates smoothly with all 4 modes.
4. **Desktop Tray**: 1-click cycling between the 4 modes.
5. **Settings GUI**: Dropdown selector with live descriptions.
