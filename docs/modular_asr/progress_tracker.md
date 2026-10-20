# Modular ASR — Progress Tracker

Created: 2026-10-19  
Last Updated: 2026-10-19  
Overall Status: **ALL PHASES COMPLETED (Phases 0–8 DONE)**

---

## Phase Gates Summary

| Phase | Title | Status | Notes |
|---|---|---|---|
| **0** | Feasibility & Discovery | ✅ DONE | Benchmarks captured; Handy cloned |
| **1** | Environment & Baseline | ✅ DONE | `transcribe-cpp==0.4.0` in `.venv`; Vulkan0 & CPU backends verified; 105 tests collected. |
| **2** | Core Abstraction (`audio_to_idea/asr/`) | ✅ DONE | `base.py` & `factory.py` with `ASRResult`, `ASRSegment`, `ASRWord`. |
| **3** | `FasterWhisperProvider` (extract & refactor) | ✅ DONE | Full CTranslate2 wrapper preserving word timestamps and Devanagari steering. |
| **4** | `TranscribeCppProvider` | ✅ DONE | Nemotron 3.5 live on RTX 3060: **138.3 ms** warm latency in `VoiceEngine`. |
| **5** | `HandyCliProvider` | ✅ DONE | Headless `/usr/bin/handy -f <wav> --json` fallback. |
| **6** | Evening Review Wake-Words (`voice_control.py`) | ✅ DONE | Fast modular provider with tiny-Whisper fallback. |
| **7** | GUI Profile Switcher | ✅ DONE | Dropdowns in `config_gui.py`, `audio_to_idea/gui.py`, and 1-click cycle in `tray_app.py`. |
| **8** | Verification & Documentation | ✅ DONE | Full test suite green (101 passed, 11 skipped); README updated; zero regressions. |

---

## Phase 0: Feasibility & Discovery (DONE 2026-10-19)

**Hardware**: NVIDIA GeForce RTX 3060 12GB — Vulkan backend active via `transcribe-cpp`.

### Benchmark Results

| Model | File | Cold Load | Inference | Speed |
|---|---|---|---|---|
| `nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf` | `input.wav` (9.6 s) | 360 ms | **142 ms** | **67.4× real-time** |
| `nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf` | `input.wav` (9.6 s) warm | — | 142 ms | 67.4× |
| `/usr/bin/handy -f input.wav --json` | `input.wav` (9.6 s) | 365 ms | 2,291 ms (incl. load) | 4.2× |
| `Voxtral-Mini-4B-Realtime-2602-Q5_K_M.gguf` | load only | **26,431 ms** | not tested | — |

> Voxtral cold load is 26 s — too slow for interactive use. Suitable for long batch processing only. Will not be the default interactive profile.

### Model Inventory (`/media/manoj/F1/models-handy/`)

| File / Dir | Format | Size | Use Case |
|---|---|---|---|
| `nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf` | GGUF (transcribe.cpp) | 751 MB | Primary fast interactive ASR |
| `parakeet-tdt-0.6b-v3-int8/` | Sherpa-ONNX (`.onnx`) | 653 MB | Future alternative (CPU-friendly) |
| `Voxtral-Mini-4B-Realtime-2602-Q5_K_M.gguf` | GGUF (transcribe.cpp) | 3.28 GB | Long batch only |

> `Whisper-Hindi2Hinglish-Apex-GGML` (Roman Hinglish): **not yet downloaded**. Must download and test `.bin` compatibility with `transcribe-cpp` before Phase 4 gate can close.

### Reference Repo Findings (`cjpais/Handy`)

Cloned to `/media/manoj/datadisk_linux/pythonprojects/Handy`. Key modules identified:

| Module | What we learn from it |
|---|---|
| `src-tauri/src/catalog/mod.rs` | How GGUF model capabilities are probed and catalogued |
| `src-tauri/src/clipboard.rs` | Wayland (`ydotool`, `wl-copy`) vs X11 clipboard & paste logic |
| `src-tauri/src/audio_toolkit/` | Silero VAD integration, ring-buffer streaming, VAD state machine |
| `src-tauri/src/transcription_coordinator.rs` | Model lifecycle (load once, reuse session, explicit unload) |

### Codebase Analysis Findings

| Finding | Consequence |
|---|---|
| `audio_to_idea/config.py:validate()` hard-rejects `asr.backend != "faster-whisper"` | Must update `validate()` to accept new backends in Phase 4.3 |
| `audio_to_idea/models.py:inspect_model()` checks for CTranslate2 `model.bin` | GGUF paths must bypass `resolve_model()` entirely; `doctor()` needs a branch |
| `voice_control.py` imports `review_engine._rlog` directly | New model loading inside `WakeWordListener` must not cause circular import |
| `audio_to_idea/resources.py` inference lock is per-process/thread | `WakeWordListener` does not need to acquire this lock (separate thread, separate mic) |
| `jobs.py:release_asr_before_synthesis` defaults `True` | Can set `False` when `backend == "transcribe-cpp"` to skip the expensive unload/reload cycle |
| `transcription.py:Transcriber.transcribe()` returns a chunk dict, not `ASRResult` | Compatibility bridge needed; `merging.py` and `jobs.py` must not change |

---

## Phase 1: Environment & Baseline

Tasks from `implementation_steps.md §Phase 1`

- [ ] 1.1 — Resolve pytest `langdetect` import
- [ ] 1.2 — Confirm 92 tests pass
- [ ] 1.3 — `uv pip install transcribe-cpp` in project `.venv`
- [ ] 1.4 — Confirm Vulkan backend in project venv
- [ ] 1.5 — Record versions

*Evidence to record:*
- pytest output line count and pass/fail summary
- `transcribe_cpp.__version__`
- Python version in `.venv`

---

## Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-10-19 | New code lives in `audio_to_idea/asr/` only | No root-level pollution; shared across all three subsystems |
| 2026-10-19 | Chunk size increases to 120 s for `transcribe-cpp` backend | Fewer seam stitches; transducer has no 30 s limit |
| 2026-10-19 | `HandyCliProvider` needs a WAV file, not raw PCM | Handy `--transcribe-file` accepts WAV only; all callers already have a WAV |
| 2026-10-19 | Voxtral is batch-only (26 s load time) | Too slow for interactive wake-word or dictation |
| 2026-10-19 | Word timestamps estimated proportionally for Nemotron | Nemotron/transducer models don't emit word-level timing; proportional OK for citations; SRT quality lower — document this |
| 2026-10-19 | `Whisper-Hindi2Hinglish-Apex` must be tested before Phase 4 closes | Unknown `.bin` compatibility with `transcribe-cpp` 0.4.0 |
