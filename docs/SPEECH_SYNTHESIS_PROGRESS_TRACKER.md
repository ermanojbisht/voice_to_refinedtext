# Universal Speech Synthesis Progress Tracker

**Document Version:** 1.0.0  
**Last Updated:** 2026-10-20  
**Current Active Branch:** `after_hany_new_update`  
**Execution Strategy:** Test-Driven Development (TDD) • Modular Architecture • Zero Downtime  

---

## Overall Status Summary

| Phase | Description | Automated Tests Status | Implementation Status | Overall |
| :--- | :--- | :---: | :---: | :---: |
| **Phase 0** | **Security & Secrets Hardening** | ✅ 5 / 5 Passing | ✅ Complete | **DONE** |
| **Phase 1** | **Speech Text Preprocessor & Normalizer** | ✅ 9 / 9 Passing | ✅ Complete | **DONE** |
| **Phase 2** | **Modular TTS Engine Dispatcher** | ✅ 7 / 7 Passing | ✅ Complete | **DONE** |
| **Phase 3** | **CLI, Markdown Narration & REST API** | ✅ 4 / 4 Passing | ✅ Complete | **DONE** |
| **Phase 4** | **Verification, Docs & Manual Rebuild** | ✅ 305+ Passing | ✅ Complete | **DONE** |

---

## Granular Checklists

### Phase 0: Security & Secrets Hardening (COMPLETED)
- [x] **0.1** Add `.secrets.json`, `.secrets/`, `.env`, and `*.secret` to `.gitignore`.
- [x] **0.2** Build `pwd_helper/secrets.py` for multi-source secrets resolution.
- [x] **0.3** Migrate existing Telegram credentials to local `.secrets.json`.
- [x] **0.4** Remove plaintext credentials from `review_config.json`.
- [x] **0.5** Update `telegram_service.py` to resolve credentials securely.
- [x] **0.6** Write `tests/test_secrets_resolver.py` (5/5 passing).
- [x] **0.7** Full test suite check (286/286 non-desktop tests passing).

---

### Phase 1: Speech Text Preprocessor & Normalizer (COMPLETED)
- [x] **1.1 (TDD)** Write automated test suite `tests/test_tts_normalizer.py`:
  - [x] Test Obsidian YAML frontmatter removal.
  - [x] Test Markdown formatting stripping (headings, bold, italics, links, blockquotes).
  - [x] Test Checkbox task narration conversion (`- [ ]` $\rightarrow$ "To do:", `- [x]` $\rightarrow$ "Completed:").
  - [x] Test Table extraction & emoji / symbol filtering.
  - [x] Test Indian currency expansion (`₹500`, `₹1.5 lakh`, `₹2.5 crore`).
  - [x] Test Engineering units (`km`, `m3`, `mm`, `MT`).
  - [x] Test PWD acronym pronunciation (`DPR`, `MB`, `NIT`, `BOQ`).
  - [x] Test Language & script detection (`en`, `hi_devanagari`, `hi_latin_hinglish`).
- [x] **1.2 (Impl)** Implement `pwd_helper/tts/normalizer.py`.
- [x] **1.3 (Verify)** Run `tests/test_tts_normalizer.py` (9/9 passing).

---

### Phase 2: Modular TTS Engine Dispatcher (COMPLETED)
- [x] **2.1 (TDD)** Write automated test suite `tests/test_tts_dispatcher.py` & `tests/test_tts_review_integration.py`:
  - [x] Test dispatcher backend discovery & priority.
  - [x] Test fallback chain (`piper` $\rightarrow$ `espeak`).
  - [x] Test script-aware model routing (Devanagari vs English).
  - [x] Test thread-safe active speech cancellation and PID cleanup.
  - [x] Test blocking vs non-blocking playback.
  - [x] Test replay cache.
- [x] **2.2 (Impl)** Build `pwd_helper/tts/` package:
  - [x] `pwd_helper/tts/__init__.py`
  - [x] `pwd_helper/tts/dispatcher.py`
  - [x] `pwd_helper/tts/backends/base.py`
  - [x] `pwd_helper/tts/backends/piper_backend.py`
  - [x] `pwd_helper/tts/backends/espeak_backend.py`
- [x] **2.3 (Integration)** Delegate `review_engine.narrate()` to `pwd_helper.tts.speak()`.
- [x] **2.4 (Verify)** Run `tests/test_tts_dispatcher.py` and `tests/test_review_web.py` (all passing).

---

### Phase 3: CLI, Markdown Narration & REST API Endpoints (COMPLETED)
- [x] **3.1 (TDD)** Write automated test suite `tests/test_tts_cli_and_api.py`:
  - [x] Test CLI `--speak "text"`.
  - [x] Test CLI `--speak-file path/to/note.md`.
  - [x] Test CLI `--stop-speech`.
  - [x] Test CLI `--listen --read-result`.
  - [x] Test REST API `POST /api/tts/speak`.
  - [x] Test REST API `POST /api/tts/stop`.
  - [x] Test REST API `GET /api/tts/status`.
- [x] **3.2 (Impl)** Enhance `pwd_cli.py` with speech flags & read-result flag.
- [x] **3.3 (Impl)** Expose TTS REST endpoints in `settings_server.py`.
- [x] **3.4 (Impl)** Add shell aliases (`v-speak`, `v-read`, `v-stop`) to `scripts/terminal_voice.sh` and `~/.zsh/aliases.zsh`.
- [x] **3.5 (Verify)** Run `tests/test_tts_cli_and_api.py` (4/4 passing).

---

### Phase 4: Full Verification, Documentation & Manual Compilation (COMPLETED)
- [x] **4.1 (Verification)** Run complete test suite across all modules (305+ tests).
- [x] **4.2 (Docs)** Update `docs/CONFIGURATION_GUIDE.md` with new TTS settings and flags.
- [x] **4.3 (Manual Rebuild)** Run `ManualService.generate_html_manual()` to regenerate `docs/generated/manual.html`.
- [x] **4.4 (Doc Tests)** Verify `tests/test_settings_web.py::test_manual_auto_rebuild_on_doc_change` passes.
