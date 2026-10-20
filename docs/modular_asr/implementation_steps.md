# Modular ASR — Implementation Steps

Created: 2026-10-19  
Status: Ready for Phase 1

---

## Phase 1 — Environment & Baseline (no new features)

Goal: working test harness + `transcribe-cpp` qualified in the project venv.

- [ ] **1.1** Fix pytest collection error: `tests/regression/test_legacy.py` imports `utils` which imports `langdetect`. Install `langdetect==1.0.9` into `.venv`, or add a conftest skip guard for machines where it is unavailable.
- [ ] **1.2** Run `pytest --ignore=tests/regression/test_legacy.py` and confirm the 92 other tests pass (or document which are skipped and why).
- [ ] **1.3** Install `transcribe-cpp` into the project `.venv` via `uv pip install transcribe-cpp`.
- [ ] **1.4** Smoke-test Vulkan initialisation: `python -c "import transcribe_cpp; print(transcribe_cpp.backends())"` must show `Vulkan0` on the RTX 3060.
- [ ] **1.5** Record which Python version and `transcribe-cpp` version are in `.venv` in `progress_tracker.md`.

*Exit gate: `pytest` collects 93+ tests with 0 errors. `transcribe-cpp` imports cleanly in the project venv.*

---

## Phase 2 — Core Abstraction: `audio_to_idea/asr/`

Goal: shared data contracts and factory wiring. No behaviour change yet.

- [ ] **2.1** Create `audio_to_idea/asr/__init__.py` (exports `factory`, `BaseASRProvider`, `ASRResult`, `ASRSegment`, `ASRWord`).
- [ ] **2.2** Create `audio_to_idea/asr/base.py` with `ASRWord`, `ASRSegment`, `ASRResult` dataclasses and abstract `BaseASRProvider` (see `plan.md §4`).
- [ ] **2.3** Create `audio_to_idea/asr/factory.py` with:
  - `from_settings(settings)` — for `audio_to_idea` batch use
  - `from_engine_config(config)` — for `engine.py` (reads `ASR_ENGINE` / `MODEL_PROFILES`)
  - `from_wake_word_config()` — for `voice_control.py` (tiny fast model, no GPU conflict)
  - Fallback chain: `TranscribeCpp → HandyCli → FasterWhisper`
- [ ] **2.4** Write unit tests in `tests/audio_to_idea/test_asr_base.py` covering: mock provider contract, factory fallback when provider unavailable.

*Exit gate: tests pass with mock provider; no existing tests broken.*

---

## Phase 3 — `FasterWhisperProvider` (zero behaviour change)

Goal: extract existing Whisper logic into the new provider shape. This is a refactor, not a feature.

- [ ] **3.1** Create `audio_to_idea/asr/faster_whisper.py` implementing `BaseASRProvider`:
  - `load()`: mirrors current `Transcriber._load()` — `WhisperModel(path, device, compute_type, cpu_threads)`, with CUDA → CPU fallback.
  - `transcribe(pcm)`: mirrors current `Transcriber.transcribe()` — language auto-detect, word timestamps, `vad_filter=True`, `initial_prompt=glossary`.
  - Includes Hindi-family re-transcription and Devanagari prompt steering (moved from `engine.py`).
  - `close()`: `self._model = None; gc.collect()` (exact copy of current `Transcriber.close()`).
- [ ] **3.2** Update `audio_to_idea/transcription.py` `Transcriber` to delegate to `FasterWhisperProvider` when `settings['asr']['backend'] == 'faster-whisper'`. Output dict shape unchanged.
- [ ] **3.3** Update `engine.py` `VoiceEngine.whisper_model` property: if `ASR_ENGINE` is absent in config, continue using `WhisperModel` directly (zero change). If `ASR_ENGINE` is present, delegate to `factory.from_engine_config()`.
- [ ] **3.4** Run full test suite. All existing tests must pass.

*Exit gate: full pytest green. Behaviour identical to pre-change on any machine without `transcribe-cpp`.*

---

## Phase 4 — `TranscribeCppProvider`

Goal: new fast inference path for Nemotron, Whisper-GGML, and Voxtral.

- [ ] **4.1** Create `audio_to_idea/asr/transcribe_cpp.py` implementing `BaseASRProvider`:
  - `is_available()`: try `import transcribe_cpp`; return `False` on `ImportError`.
  - `load()`: `self._model = transcribe_cpp.Model(path)` — warm on first call; subsequent calls are no-ops.
  - `transcribe(pcm)`: `session = self._model.session(); result = session.run(pcm)`. Convert `result.text` + any segment data to `ASRResult`.
  - Word timestamps: Nemotron/Voxtral do not return word-level timing. Estimate proportionally: split `result.text` by whitespace; distribute uniformly within the segment time range.
  - Language: attach `result.lang` (if model supports; else `None`).
  - `close()`: `self._model.close(); self._model = None`.
- [ ] **4.2** Handle `family` routing in profile: `"whisper"` / `"nemotron"` / `"voxtral"` all use the same `transcribe_cpp.Model(path)` — no special routing needed. The GGUF/bin format is self-describing.
- [ ] **4.3** Update `audio_to_idea/config.py` `validate()`: accept `'transcribe-cpp'` in `SUPPORTED_ASR_BACKENDS`. Add `active_profile` and `model_profiles` to `DEFAULTS['asr']`.
- [ ] **4.4** Update `audio_to_idea/models.py` `doctor()`: when backend is `transcribe-cpp`, skip `inspect_model()` (it checks for CTranslate2 layout) and instead verify the file exists and has a non-zero size.
- [ ] **4.5** Adjust default `chunk_seconds` to `120.0` when backend is `transcribe-cpp` (reduce seam count on long files without changing the chunking contract).
- [ ] **4.6** Write integration tests in `tests/audio_to_idea/test_transcribe_cpp_provider.py`: use the live Nemotron model at `/media/manoj/F1/models-handy/nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf`; skip if model file absent. Assert text is non-empty and `latency_ms < 2000`.

*Exit gate: `FasterWhisperProvider` tests still pass. `TranscribeCppProvider` test passes on the development machine.*

---

## Phase 5 — `HandyCliProvider`

Goal: zero-Python-dependency fallback using the installed `/usr/bin/handy` binary.

- [ ] **5.1** Create `audio_to_idea/asr/handy_cli.py` implementing `BaseASRProvider`:
  - `is_available()`: check `shutil.which('handy')` is not None.
  - `load()`: no-op (binary is always ready).
  - `transcribe(pcm, wav_path=None)`: if `wav_path` is provided write PCM to it; else write to a temp file. Call `handy -f <path> --json`. Parse JSON stdout for `text`, `audio_secs`, `best_ms`.
  - Returns single-segment `ASRResult` with `words=[]`.
  - `close()`: no-op.
- [ ] **5.2** Since this provider needs a WAV file path, the factory `from_engine_config()` must pass `wav_path=self.script_dir/input.wav` when creating this provider for `engine.py`. The `transcription.py` path already has a `prepared.wav`.
- [ ] **5.3** Write a test that skips if `/usr/bin/handy` is absent; otherwise transcribes `input.wav` and asserts a non-empty result.

*Exit gate: provider works end-to-end on development machine. Fallback chain tested.*

---

## Phase 6 — Evening Review Wake-Words (`voice_control.py`)

Goal: replace hardcoded tiny-Whisper with the pluggable provider.

- [ ] **6.1** Update `WakeWordListener._load_model()` in `voice_control.py`:
  - Try `factory.from_wake_word_config()` first (returns `TranscribeCppProvider` with active profile, or `FasterWhisperProvider("tiny")` as last resort).
  - Wrap in try/except so any failure falls back to the existing `WhisperModel("tiny")` code path.
- [ ] **6.2** Update `WakeWordListener._run()` to call `self._provider.transcribe(audio)` instead of `self._model.transcribe(audio, ...)`.
- [ ] **6.3** Verify no circular import: `voice_control.py → audio_to_idea.asr.factory → audio_to_idea.asr.faster_whisper → faster_whisper` (OK). Confirm `review_engine` is not imported from `audio_to_idea`.

*Exit gate: Evening Review starts, narration plays, "stop" / "आगे" wake-words trigger correctly.*

---

## Phase 7 — GUI: Model Profile Switcher

Goal: users can switch ASR profiles from the settings GUI without editing JSON.

- [ ] **7.1** Add ASR profile dropdown to `config_gui.py` (Voice Refiner settings panel): lists keys from `MODEL_PROFILES`, shows current `ACTIVE_MODEL_PROFILE`.
- [ ] **7.2** Add ASR backend/profile selector to `audio_to_idea/gui.py` Settings tab: lists `asr.active_profile` values from `model_profiles`.
- [ ] **7.3** Display active engine name and last inference latency in the tray app tooltip (read from `log.json` last entry).
- [ ] **7.4** Show a notification/warning in the GUI when `TranscribeCppProvider` is not available (`is_available() == False`), suggesting `pip install transcribe-cpp`.

*Exit gate: switch profile in GUI, restart tray, confirm new ASR model is used.*

---

## Phase 8 — Verification & Documentation

Goal: clean test suite, updated README, and no regressions.

- [ ] **8.1** Run full `pytest` — all 93+ tests pass.
- [ ] **8.2** End-to-end test: Voice Refiner hotkey → Nemotron → Ollama → clipboard paste.
- [ ] **8.3** End-to-end test: `python3 -m audio_to_idea process --input <30min.mp3>` with `transcribe-cpp` backend completes within 90 s on the RTX 3060.
- [ ] **8.4** Evening Review: start session, narrate 3 steps, use "stop" and "आगे" wake-words.
- [ ] **8.5** Regression: switch back to `faster-whisper` profile; confirm full pipeline still works.
- [ ] **8.6** Update `README.md` — add ASR engine section; document `MODEL_PROFILES` config keys.
- [ ] **8.7** Update `docs/modular_asr/progress_tracker.md` to DONE.

*Exit gate: all gates above are green. No known regressions.*
