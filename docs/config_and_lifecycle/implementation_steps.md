# Configuration Management, VRAM Lifecycle & User Guide — Implementation Steps

**Target:** Phased delivery of VRAM keep-alive control, background pre-warming, and configuration manual.

---

## Phase 1 — VRAM Lifecycle Backend (`utils.py`, `engine.py`, `config.json`)

- [ ] **1.1** Update `utils.py:call_ollama()`:
  - Add `keep_alive: str = "5m"` argument to `call_ollama`.
  - Include `"keep_alive": keep_alive` in the JSON request payload sent to `{host}/api/generate`.
- [ ] **1.2** Update `engine.py:refine()`:
  - Read `keep_alive = self.config.get("OLLAMA_KEEP_ALIVE", "5m")`.
  - Pass `keep_alive=keep_alive` to `utils.call_ollama(...)`.
- [ ] **1.3** Update `review_engine.py`:
  - When calling `utils.call_ollama()`, ensure it passes the configured `keep_alive` (inheriting from `review_config.json` or `config.json`).
- [ ] **1.4** Update `config.json`:
  - Add `"OLLAMA_KEEP_ALIVE": "5m"` (or `"60m"` on the development machine).
- [ ] **1.5** Write unit tests:
  - Verify that `call_ollama` properly sends `"keep_alive"` in its request body.
  - Verify fallback to `"5m"` when not specified.

*Gate: Unit tests pass; keep_alive payload verified with mock/live Ollama.*

---

## Phase 2 — Background Eager Pre-Warming (`tray_app.py`)

- [ ] **2.1** Implement `VoiceAssistantTray._background_prewarm()` in `tray_app.py`:
  - Launch inside a daemon thread after tray icon setup.
  - Step A: Transcribe 0.1s silence (`np.zeros(1600, dtype=np.float32)`) via `self.engine.asr_provider` to trigger Vulkan compute shader JIT compilation.
  - Step B: Check `keep_alive = self.engine.config.get("OLLAMA_KEEP_ALIVE", "5m")`. If `keep_alive != "0"`, send a 1-token prompt (`"ready"`) to Ollama with the configured `keep_alive` to bring model weights into GPU VRAM.
  - Wrap both steps in robust `try...except` so background pre-warming is strictly non-blocking and fail-safe.
- [ ] **2.2** Verify in `review_debug.log` that pre-warming completes cleanly in the background within ~15s of tray app launch.
- [ ] **2.3** Verify that the subsequent first hotkey recording completes in **< 1s** without the 33s cold-start delay.

*Gate: First audio is instant; tray app UI starts immediately with zero delay.*

---

## Phase 3 — Settings GUI Controls (`config_gui.py`)

- [ ] **3.1** In `config_gui.py:_build_voice_tab()`:
  - Under "⚙️ AI Parameters", add an **Ollama Keep-Alive** combobox.
  - Options:
    - `"0 (Immediate unload — Low VRAM)"`
    - `"2m"`
    - `"5m (Default)"`
    - `"15m"`
    - `"60m (Work session)"`
    - `"-1 (Keep resident in VRAM)"`
  - Populate initial value matching `self.main_cfg.get("OLLAMA_KEEP_ALIVE", "5m")`.
- [ ] **3.2** In `config_gui.py:_save_all()`:
  - Extract the clean keep-alive code (e.g. `"0"`, `"2m"`, `"5m"`, `"60m"`, `"-1"`).
  - Persist `"OLLAMA_KEEP_ALIVE"` into `config.json`.
- [ ] **3.3** Verify GUI settings load and save round-trip cleanly without throwing exceptions.

*Gate: User can switch keep-alive from GUI; `config.json` reflects choices accurately.*

---

## Phase 4 — Comprehensive User Manual (`docs/CONFIGURATION_GUIDE.md`)

- [ ] **4.1** Author `docs/CONFIGURATION_GUIDE.md`:
  - Quick-start hardware presets (High-End GPU, Low-VRAM/Office PC, Hindi Translation Specialist).
  - Comprehensive field-by-field reference for:
    - `config.json` (Voice Refiner)
    - `review_config.json` (Evening Review)
    - `audio_to_idea_config.json` (Audio to Ideas)
  - Clear explanation of VRAM tradeoffs for `OLLAMA_KEEP_ALIVE`.
  - Calibration guide for microphone silence threshold (`SILENCE_THRESHOLD`).
  - Wayland (`ydotool`) vs X11 (`xdotool`) setup and troubleshooting.
- [ ] **4.2** Add cross-links in `README.md` pointing to `docs/CONFIGURATION_GUIDE.md`.

*Gate: Complete, accurate, easily readable documentation.*

---

## Phase 5 — Verification & Automated Regression Testing

- [ ] **5.1** Run full pytest test suite — all 101+ tests pass with zero regressions.
- [ ] **5.2** Verify live dictation test through tray app with Nemotron + Ollama keep-alive.
- [ ] **5.3** Update `docs/config_and_lifecycle/progress_tracker.md` to DONE.

*Gate: Green test suite, verified live dictation, completed tracker.*
