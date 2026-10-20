# Configuration Management, VRAM Lifecycle & User Guide — Architecture Plan

**Created:** 2026-10-19  
**Status:** In Review / Ready for Implementation  
**Target Environments:**
- Home PC: Ubuntu 26.04 LTS, Python 3.14, NVIDIA GeForce RTX 3060 12GB (Vulkan)
- Office PC: Ubuntu 22.04 LTS, Python 3.10, Low-VRAM / Shared GPU / CPU

---

## 1. Executive Summary & Problem Statement

Our recent telemetry from live testing confirmed two critical operational realities:

1. **The Double Cold-Start Phenomenon**:
   - On the very first audio recording after app launch, transcription took **15.0s** (Vulkan shader JIT compilation) and Ollama refinement took **18.0s** (disk-to-VRAM loading of `qwen2.5:3b`), totaling **~33 seconds**.
   - Subsequent recordings ran in **< 0.5s total** because models remained hot in VRAM.
   - **Goal**: Pre-warm both models in a non-blocking background thread on app boot so the first recording is as fast as all subsequent ones.

2. **VRAM Resource Asymmetry (Home vs Office PC)**:
   - On high-VRAM machines (RTX 3060 12GB), keeping the LLM permanently in VRAM (`keep_alive: "60m"` or `"-1"`) is optimal.
   - On lower-VRAM machines (e.g. 4GB–6GB or office desktops), leaving an LLM resident can lock display servers, cause swapping, or starve other applications.
   - **Goal**: Make `OLLAMA_KEEP_ALIVE` configurable via `config.json` and `config_gui.py`, supporting immediate offloading (`"0"`) for low-VRAM machines and prolonged caching (`"60m"`) for high-performance setups.

3. **Configuration Complexity & Documentation Gap**:
   - The application now manages settings across three distinct subsystems:
     - Core Voice Refiner (`config.json`)
     - Evening Review & Daily Reflection (`review_config.json`)
     - Audio to Ideas Batch Processor (`audio_to_idea_config.json`)
   - Users need a definitive, copy-paste ready User Manual (`docs/CONFIGURATION_GUIDE.md`) with hardware presets, field-by-field explanations, and tuning tips.

---

## 2. Technical Architecture & Component Design

### 2.1 Configurable Ollama Keep-Alive (`OLLAMA_KEEP_ALIVE`)

Ollama's `/api/generate` endpoint accepts a `keep_alive` field:
- `"0"`: Unloads the model immediately after response completion (crucial for low-VRAM PCs).
- `"2m"` / `"5m"`: Standard idle timers before automatic VRAM eviction.
- `"60m"`: Retains the model for an entire work session.
- `"-1"`: Never unloads until Ollama restarts or an explicit unload request is received.

#### Data Contract Updates:
1. **`config.json`**:
   ```json
   {
       "OLLAMA_KEEP_ALIVE": "5m"
   }
   ```
2. **`utils.py:call_ollama()`**:
   ```python
   def call_ollama(host, model, prompt, stop_tokens, temperature=0.1, timeout=120, keep_alive="5m"):
       payload = {
           "model": model,
           "prompt": prompt,
           "stream": False,
           "temperature": temperature,
           "top_p": 0.9,
           "stop": stop_tokens,
           "keep_alive": keep_alive
       }
   ```
3. **`engine.py:refine()`**:
   ```python
   keep_alive = self.config.get("OLLAMA_KEEP_ALIVE", "5m")
   response = utils.call_ollama(
       self.config.get("OLLAMA_HOST"), model_name, prompt, stops,
       self.config.get("TEMPERATURE", 0.1),
       keep_alive=keep_alive
   )
   ```

---

### 2.2 Background Eager Pre-Warming Engine

In `tray_app.py`, immediately after initializing the tray icon, launch a non-blocking daemon thread:

```python
def _background_prewarm(self):
    """Pre-compiles Vulkan shaders and pre-loads Ollama LLM into VRAM."""
    _tlog("Background pre-warm started")
    try:
        # 1. Pre-warm active ASR engine (compiles Vulkan compute shaders)
        if self.engine.asr_provider:
            dummy_pcm = np.zeros(1600, dtype=np.float32)  # 0.1s silence
            self.engine.asr_provider.transcribe(dummy_pcm)
            _tlog("ASR pre-warm complete (Vulkan shaders cached)")

        # 2. Pre-warm Ollama LLM (only if keep_alive != '0')
        keep_alive = self.engine.config.get("OLLAMA_KEEP_ALIVE", "5m")
        if str(keep_alive).strip().lower() not in {"0", "0s", "none"}:
            host = self.engine.config.get("OLLAMA_HOST", "http://localhost:11434")
            model = self.engine.config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")
            _utils.call_ollama(host, model, "ready", stop_tokens=[], keep_alive=keep_alive)
            _tlog(f"Ollama pre-warm complete (model={model}, keep_alive={keep_alive})")
    except Exception as exc:
        _tlog(f"Background pre-warm non-fatal notice: {exc}")
```

#### Pre-Warm Guarantees:
- **Zero UI Block**: The tray icon appears instantly; user interaction is never delayed.
- **Fail-Safe**: Any network or GPU initialization errors in the thread are caught and logged without crashing the tray.
- **VRAM Respect**: If `OLLAMA_KEEP_ALIVE` is `"0"`, the LLM is NOT pre-warmed, keeping VRAM free on low-resource machines.

---

### 2.3 Graphical Settings UI (`config_gui.py`)

In the **AI Parameters** section of `config_gui.py`:
- Add an **Ollama Keep-Alive** combobox with presets:
  - `0 (Immediate unload — Low VRAM)`
  - `2m`
  - `5m (Default)`
  - `15m`
  - `60m (Work session)`
  - `-1 (Keep resident in VRAM)`
- Value mapping on save: extracts the prefix or clean string to save clean format (`"0"`, `"5m"`, `"60m"`, `"-1"`) in `config.json`.

---

### 2.4 Comprehensive Configuration User Manual (`docs/CONFIGURATION_GUIDE.md`)

A comprehensive, beautifully formatted Markdown manual structured as:

1. **System Overview & Architecture Map**: Highlighting the 3 config files.
2. **Ready-to-Use Hardware Presets**:
   - *Preset 1: High-Performance GPU Workstation* (RTX 3060 12GB+, Nemotron fast, Ollama keep-alive 60m, Wayland/X11 typing).
   - *Preset 2: Low-VRAM / Office Desktop* (Ubuntu 22.04, 4GB VRAM or CPU, Whisper turbo / Nemotron CPU, Ollama keep-alive 0/2m).
   - *Preset 3: Bilingual Hindi/English Specialist* (Devanagari script steering vs Latin Hinglish Apex).
3. **Core Voice Refiner Reference (`config.json`)**: Every key documented with Type, Default, Valid Values, and Performance Impact.
4. **Evening Review Reference (`review_config.json`)**: Vault paths, Piper neural TTS setup, voice wake-word thresholds, Telegram bot config, per-step reflection schema.
5. **Audio to Ideas Reference (`audio_to_idea_config.json`)**: Processing modes, custom prompt folders, VAD chunking, output formats.
6. **Calibration & Troubleshooting Guide**:
   - Calibrating `SILENCE_THRESHOLD` for quiet vs noisy rooms.
   - Troubleshooting Wayland typing (`ydotool` socket setup) vs X11 (`xdotool`).
   - Resolving Ollama VRAM exhaustion on tight GPUs.

---

## 3. Compatibility & Quality Guardrails

1. **Python 3.10–3.14 Compatibility**:
   - `from __future__ import annotations` in all Python files.
   - No `match/case` syntax.
   - Tuple-based `isinstance(x, (A, B))` checks.
2. **Comment & Docstring Preservation**:
   - All existing comments, docstrings, and logic preserved.
3. **Automated Verification**:
   - All 101 unit tests must remain 100% green.
   - Unit tests for `call_ollama` keep_alive parameter added.
