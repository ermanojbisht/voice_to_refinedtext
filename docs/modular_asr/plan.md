# Modular High-Performance ASR Engine — Plan

Created: 2026-10-19  
Last revised: 2026-10-19 (deep code + Handy codebase review)  
Status: Planning approved — ready for Phase 1 execution  
Delivery: Pluggable ASR subsystem supporting Nemotron / Whisper-GGML / Voxtral / faster-whisper across all three subsystems, compatible with Ubuntu 22.04 (Python 3.10) and Ubuntu 26.04 (Python 3.14).

**Reference repo:** `/media/manoj/datadisk_linux/pythonprojects/Handy` (upstream `cjpais/Handy`)  
**Related docs:** [`implementation_steps.md`](implementation_steps.md) · [`progress_tracker.md`](progress_tracker.md)

---

## 1. Context & Motivation

### What currently exists and where it is hardcoded

| Subsystem | File | ASR today | Hardcoding point |
|---|---|---|---|
| Voice Refiner (hotkey dictation) | `engine.py` `VoiceEngine.whisper_model` | `faster_whisper.WhisperModel` lazy-loaded, HF ID from `config.json["WHISPER_MODEL"]` | lines 27-39 |
| Evening Review — voice commands | `voice_control.py` `WakeWordListener._load_model()` | `WhisperModel("tiny", cpu, int8)` | line 74 |
| Audio to Ideas (batch) | `audio_to_idea/transcription.py` `Transcriber._load()` | `WhisperModel(model_info["path"], device, compute_type)` | lines 21-38 |
| Audio to Ideas config validator | `audio_to_idea/config.py` `validate()` | Raises on `asr.backend != "faster-whisper"` | line 155-156 |
| Audio to Ideas model inspector | `audio_to_idea/models.py` `inspect_model()` | Checks for CTranslate2 `model.bin` — rejects GGUF paths | lines 21-43 |
| Audio to Ideas chunk size | `audio_to_idea/config.py` `DEFAULTS` | Fixed `chunk_seconds: 60.0` regardless of backend capability | line 26 |

### Why change

1. **Speed**: Nemotron 3.5 (0.6B Q8_0 GGUF) on Vulkan (RTX 3060) = 142 ms for a 9.6 s clip, 67.4x real-time. Whisper large-v3-turbo ≈ 1.5–3 s for same clip.
2. **VRAM**: Whisper large-v3 ≈ 3 GB VRAM → forces explicit `release_asr_before_synthesis` guard before every Ollama call in `jobs.py`. Nemotron ≈ 800 MB → both stay resident together on 12 GB card.
3. **Hallucination loops**: Whisper (autoregressive encoder-decoder) repeats phrases during silences. Nemotron / Parakeet (streaming transducer, RNN-T) emit token-by-token and cannot loop.
4. **Roman-script Hinglish**: `Whisper-Hindi2Hinglish-Apex-GGML` fine-tuned Whisper emits `"kya haal hai"` rather than Devanagari. Needs GGML (`.bin`) loader — CTranslate2 cannot run GGML weights.
5. **Long-file throughput**: 60-minute MP3 ≈ 4–6 min with Whisper turbo; ≈ 55 s with Nemotron. Handy's smart VAD-guided chunking (cuts at pauses, not at fixed time boundaries) also avoids word-boundary splits.

---

## 2. Ideas Adopted from Handy Codebase

Reading `cjpais/Handy`'s Rust source revealed several concrete patterns to port:

### 2a. Silero VAD with hangover tail (replaces RMS energy gate in `engine.py`)
**Source:** `src-tauri/src/audio_toolkit/vad/silero.rs`, `vad/mod.rs`, `audio/sink.rs`

Handy uses **Silero VAD** (a 1.7 MB ONNX neural network) run on CPU via `transcribe.cpp`'s ORT backend. Key parameters:
- `VAD_OFFLINE_HANGOVER_MS = 450` — silence after speech before cutting off
- `VAD_STREAMING_HANGOVER_MS = 1650` — longer tail for streaming models (partial words still arriving)
- `VAD_ONSET_MS = 60` — minimum voiced frames before declaring speech start
- Silero resets LSTM state between recordings (prevents the previous session's context bleeding in)

Our current code uses raw RMS energy (`np.sqrt(np.mean(chunk**2)) < threshold`) as the silence gate. This:
- Clips word endings (energy drops before phoneme finishes)
- Has no concept of "onset" — single loud noise triggers recording
- Has no hangover tail — abrupt cutoff

**Porting plan:** Use `webrtcvad` (pure Python, ships as a wheel for 3.10+) as an easy first drop-in, or use Silero ONNX directly via `onnxruntime` (already installed as a system lib with Handy). Silero VAD GGUF model is shipped with Handy at `/usr/lib/Handy/resources/`.

```python
# Proposed: replace RMS gate in engine.py with a SmoothedVAD wrapper
class SmoothedVAD:
    """Frame-by-frame VAD with onset counter and hangover tail.
    Prevents single noise bursts from starting recording and word-end clipping."""
    def __init__(self, threshold=0.5, onset_ms=60, hangover_ms=450, sample_rate=16000):
        ...
```

### 2b. VAD-guided chunking (smarter than fixed 60-second windows)
**Source:** `src-tauri/src/audio_toolkit/chunking.rs`

Handy cuts long audio **at silence midpoints**, not at fixed time boundaries. The algorithm:
1. Score per-frame speech probabilities from Silero VAD
2. Find all `[speech, silence, speech]` segment boundaries
3. Greedily pick cut points in the middle of pauses, aiming for 30 s chunks, max 40 s, min 5 s

**Why this matters for `audio_to_idea`**: current fixed 60-second chunking can split a sentence mid-word. VAD-guided cuts place boundaries in genuine silence, eliminating the need for overlap + fuzzy-merge deduplication in `merging.py`.

**Porting plan:** Implement `audio_to_idea/asr/vad_chunker.py` as an optional alternative to the current fixed chunker in `audio_to_idea/audio.py`. Falls back to fixed chunking if VAD is unavailable.

### 2c. Custom word correction with fuzzy n-gram matching
**Source:** `src-tauri/src/audio_toolkit/text.rs` (`apply_custom_words`)

Handy applies a post-transcription **fuzzy n-gram word corrector** — e.g. "Charge B" → "ChargeBee", "Chat G P T" → "ChatGPT", "R and D" → "R&D". Uses `word_correction_threshold = 0.18` Jaro-Winkler score. The current `audio_to_idea` profiles only supply a glossary `initial_prompt` to Whisper — helpful but unreliable. Handy's post-pass is deterministic.

**Porting plan:** Add `audio_to_idea/asr/word_corrector.py` with a simple fuzzy n-gram corrector using `rapidfuzz` (available as a wheel, pure Python, fast). Apply after any ASR provider's output before returning `ASRResult`.

### 2d. Filler word removal with language-gated word lists
**Source:** `src-tauri/src/audio_toolkit/text.rs` (`remove_filler_words`, `filter_transcription_output`)

Handy maintains **per-language filler word lists** (`uh`, `uhm` for English; `äh`, `ähm` for German; `euh` for French; universal: `hmm`, `hm`, `uhh`). Crucially, language-specific fillers only fire when language is confirmed — to avoid deleting Portuguese "um" when speaking English.

For our Hindi/Hinglish use case: `um`, `uh`, `hmm` in English; `aaa`, `हाँ हाँ`, filler `तो` at sentence start in Hindi.

**Porting plan:** Add `audio_to_idea/asr/filler_filter.py` with a two-tier system matching Handy's: universal tier (fires always) + language-gated tier (fires only when language is confirmed).

### 2e. Model unload timeout (configurable residency)
**Source:** `settings.rs` `model_unload_timeout`

Handy keeps ASR model in memory for a configurable period after last use (`never`, `min1`, `min5`, `min15`). Our `jobs.py` always unloads Whisper immediately before Ollama. With Nemotron (~800 MB), keeping the model warm between rapid dictation bursts is desirable.

**Porting plan:** Add `asr_model_unload_timeout` to config (seconds, `0` = never unload). `TranscribeCppProvider` tracks last-use time and a background thread evicts if idle.

### 2f. Clipboard and typing tool selection (better than current `wtype`/`xdotool` probe)
**Source:** `settings.rs` `TypingTool` enum, `clipboard.rs`

Handy supports: `Auto`, `Wtype`, `Ydotool`, `Xdotool`, `Kwtype` (KDE). For Linux, it detects Wayland vs X11 and picks accordingly. Our `engine.py:type_text()` already does `which wtype` / `which xdotool` probing but doesn't persist the choice — re-probes on every call. Also, **`ydotool`** is already installed and working on your Ubuntu 26.04 (confirmed in Handy logs), but our code never tries it.

**Porting plan:** Add `TYPING_TOOL: "auto" | "wtype" | "ydotool" | "xdotool" | "pynput"` to `config.json`. `engine.py:type_text()` reads this once and caches. `ydotool` should be tried before `wtype` on Wayland since Handy proves it works.

---

## 3. Ubuntu Compatibility Matrix

| Ubuntu | Python | `transcribe-cpp` | `faster-whisper` | Key concern |
|---|---|---|---|---|
| **22.04 (office)** | 3.10.x | ✅ wheel available (tested) | ✅ 1.2.1 | No `match` statements in new code; `X | Y` union type hints need `from __future__ import annotations` |
| **26.04 (home)** | 3.14.x | ✅ wheel available (tested in session) | ✅ 1.2.1 | None — works today |
| **Both** | — | `transcribe-cpp-native==0.4.0` | `ctranslate2>=4.0` | Vulkan available on 26.04 (RTX 3060); CUDA/CPU fallback for 22.04 office |

### Python 3.10 compatibility rules for all new code
1. All union type hints use `from __future__ import annotations` at top of file (enabling `str | None` syntax for 3.10).
2. No `match`/`case` statements (Python 3.10+ only but not worth the risk — use `if/elif`).
3. All dataclasses use `from __future__ import annotations` (forward references).
4. `X | Y` type expressions in `isinstance()` calls require 3.10+ — use `(X, Y)` tuples instead.
5. `tomllib` is stdlib in 3.11+; not needed here (we use JSON configs).

### Office PC (Ubuntu 22.04) additional notes
- `/usr/bin/handy` may not be installed — `HandyCliProvider.is_available()` handles this gracefully.
- Vulkan may not be available (depends on GPU). `TranscribeCppProvider` auto-selects CPU backend.
- Office machine GPU unknown — provider must not crash on CPU-only mode.

---

## 4. New Code Locations (no root-level pollution)

All new code lives inside `audio_to_idea/asr/`:

```
audio_to_idea/
└── asr/
    ├── __init__.py        # exports: factory, BaseASRProvider, ASRResult, ASRSegment, ASRWord
    ├── base.py            # abstract class + dataclasses (all comments in English)
    ├── factory.py         # builds correct provider from config; handles fallback chain
    ├── faster_whisper.py  # FasterWhisperProvider  — existing behaviour, extracted
    ├── transcribe_cpp.py  # TranscribeCppProvider  — Nemotron/Whisper-GGML/Voxtral
    ├── handy_cli.py       # HandyCliProvider       — subprocess /usr/bin/handy -f
    ├── filler_filter.py   # language-gated filler word removal (ported from Handy text.rs)
    ├── word_corrector.py  # fuzzy n-gram custom word correction (ported from Handy text.rs)
    └── vad_chunker.py     # VAD-guided silence-aware chunking (ported from Handy chunking.rs)
```

`engine.py` and `voice_control.py` are root-level and import from `audio_to_idea.asr`. Nothing new is added at the repository root.

---

## 5. Shared Output Contract

```python
# audio_to_idea/asr/base.py
from __future__ import annotations          # Python 3.10 compatibility
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np


@dataclass
class ASRWord:
    text: str
    start: float                            # seconds from audio start
    end: float
    probability: float = 1.0               # 0.0–1.0; 1.0 if model doesn't provide


@dataclass
class ASRSegment:
    id: str                                 # "S00001" (matches existing merging.py IDs)
    text: str
    start: float
    end: float
    words: list[ASRWord] = field(default_factory=list)
    avg_logprob: float = 0.0               # 0.0 if model doesn't provide
    no_speech_prob: float = 0.0           # 0.0 if model doesn't provide


@dataclass
class ASRResult:
    text: str                               # full joined transcript
    language: str | None                   # ISO-639-1 or None if model doesn't detect
    duration: float                         # audio seconds
    latency_ms: float                       # wall-clock inference time in ms
    segments: list[ASRSegment]
    backend: str                            # "faster_whisper" | "transcribe_cpp" | "handy_cli"
    model_path: str                         # for logging / tracing


class BaseASRProvider(ABC):
    """
    Pluggable ASR backend. Lifecycle: load() → transcribe() [many times] → close().

    All providers must be thread-safe: engine.py and voice_control.py may call
    transcribe() from different threads (though never concurrently — the
    legacy_inference lock in resources.py prevents that).
    """

    @abstractmethod
    def load(self) -> None:
        """Load model weights into memory. Idempotent — safe to call multiple times."""

    @abstractmethod
    def transcribe(self, pcm: np.ndarray, *,
                   language: str | None = None,
                   prompt: str | None = None) -> ASRResult:
        """
        Transcribe 16 kHz mono float32 PCM.

        Args:
            pcm:      numpy float32 array, values in [-1.0, 1.0], 16 000 Hz.
            language: ISO-639-1 hint ("en", "hi") or None for auto-detect.
            prompt:   Domain glossary or initial context (model permitting).

        Returns:
            ASRResult with text, segments, latency, and detected language.
        """

    @abstractmethod
    def close(self) -> None:
        """Release model weights. Idempotent. Must never raise."""

    def is_available(self) -> bool:
        """Return False if this provider cannot run on this machine (missing lib/binary)."""
        return True
```

### Compatibility bridge for `transcription.py` / `merging.py` / `jobs.py`

`audio_to_idea/transcription.py` today returns a chunk dict:
```python
{'index': ..., 'start': ..., 'end': ..., 'segments': [
    {'text': ..., 'start': ..., 'end': ..., 'words': [...],
     'avg_logprob': ..., 'no_speech_prob': ...}
], 'language': ..., 'device': ..., 'compute_type': ...}
```
The updated `Transcriber` will emit **this same shape** — zero changes to `merging.py` or `jobs.py`.

---

## 6. Configuration Changes

### `audio_to_idea/config.py`

**Change 1 — `validate()` (line 155-156):**
```python
# Before:
if a['backend'] != 'faster-whisper' or s['backend'] != 'ollama':
    raise ValueError('This release supports faster-whisper ASR and Ollama synthesis')

# After:
_ASR_BACKENDS = {'faster-whisper', 'transcribe-cpp', 'handy-cli'}
if a['backend'] not in _ASR_BACKENDS or s['backend'] != 'ollama':
    raise ValueError(f"ASR backend must be one of {sorted(_ASR_BACKENDS)}")
```

**Change 2 — `DEFAULTS['asr']`:** add optional fields (all `None` by default for backwards compatibility):
```python
'model_profiles': {},      # {profile_name: {backend, family, path, device}}
'active_profile': None,    # profile name; None = use legacy model_id/model_path
'chunk_seconds': 60.0,     # default; override per-backend in factory
```

**Change 3 — `DEFAULTS['asr']`:** add post-processing settings:
```python
'filler_removal': True,    # enable language-gated filler word removal
'custom_words': [],        # fuzzy-corrected after transcription (like Handy's custom_words)
'word_correction_threshold': 0.18,  # Jaro-Winkler threshold (Handy default)
```

### `config.json` (Voice Refiner)

New top-level keys — fully backwards-compatible (missing = existing `WHISPER_MODEL` behaviour unchanged):
```json
{
  "ASR_ENGINE": "transcribe_cpp",
  "ACTIVE_MODEL_PROFILE": "nemotron_fast",
  "TYPING_TOOL": "auto",
  "MODEL_PROFILES": {
    "nemotron_fast": {
      "backend": "transcribe_cpp",
      "family": "nemotron",
      "path": "/media/manoj/F1/models-handy/nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf",
      "device": "auto"
    },
    "hinglish_apex": {
      "backend": "transcribe_cpp",
      "family": "whisper",
      "path": "/path/to/Whisper-Hindi2Hinglish-Apex-Q8.bin",
      "device": "auto",
      "note": "Roman-script Hinglish; emits Latin script not Devanagari"
    },
    "whisper_turbo": {
      "backend": "faster_whisper",
      "path": "large-v3-turbo",
      "device": "auto"
    },
    "voxtral_batch": {
      "backend": "transcribe_cpp",
      "family": "voxtral",
      "path": "/media/manoj/F1/models-handy/Voxtral-Mini-4B-Realtime-2602-Q5_K_M.gguf",
      "device": "auto",
      "note": "26s cold load — batch processing only, not for live dictation"
    }
  }
}
```

---

## 7. Three Concrete Providers

### A. `FasterWhisperProvider` (zero behaviour change; pure extract-and-refactor)

Wraps existing logic from `engine.py` and `transcription.py`:
- Hindi-family re-transcription (Devanagari prompt steering) migrates here from `engine.py`.
- Word timestamps preserved for `audio_to_idea` citation markers.
- `close()` = `self._model = None; gc.collect()` (identical to current `Transcriber.close()`).

### B. `TranscribeCppProvider` (new; primary fast path)

- `is_available()`: `import transcribe_cpp` — `False` on `ImportError`.
- `load()`: `transcribe_cpp.Model(path)`. After first call, model is warm; subsequent loads are no-ops.
- `transcribe(pcm)`: `session = self._model.session(); result = session.run(pcm)`. First call ~360 ms (GPU upload); subsequent calls ~142 ms.
- Word timestamps: Nemotron/transducer models don't emit per-word timing. Estimated proportionally by character count within each segment. Good enough for `txt`/`json`; SRT/VTT quality is lower — documented and warned in GUI.
- Language: `result.lang` when model supports; else `None`.
- Chunking: when `active_profile.family` is `"nemotron"` or `"voxtral"`, factory sets `chunk_seconds = 120.0` automatically.
- `close()`: `self._model.close(); self._model = None`.
- Note: GGUF and GGML `.bin` formats are both self-describing in `transcribe.cpp` — same API, no special routing needed.

### C. `HandyCliProvider` (subprocess fallback; zero Python deps)

- `is_available()`: `shutil.which('handy') is not None`.
- `load()`: no-op (binary always ready).
- `transcribe(pcm, *, wav_path)`: writes PCM to `wav_path` (or temp file), calls `handy -f <path> --json`, parses `{"text": ..., "audio_secs": ..., "best_ms": ...}`.
- Returns single-segment `ASRResult` (`words=[]`).
- **Limitation**: needs a WAV file path. All callers already have one (`input.wav` in engine, `prepared.wav` in batch processor).

### Fallback chain (automatic, transparent to callers)

```
factory.from_settings(settings) / from_engine_config(config):
    1. Try TranscribeCppProvider — if is_available() and model file exists
    2. Try HandyCliProvider     — if /usr/bin/handy exists
    3. Always available: FasterWhisperProvider
```

---

## 8. Subsystem Integration Details

### A. `engine.py` — Voice Refiner

Current `transcribe()` is decorated `@legacy_inference` (acquires cross-process coordination lock). New code keeps this decorator:

```python
@property
def _asr_provider(self):
    """Lazy-build provider from config. Cached for the lifetime of the engine."""
    if self.__asr_provider is None:
        from audio_to_idea.asr import factory
        self.__asr_provider = factory.from_engine_config(self.config)
    return self.__asr_provider

@legacy_inference
def transcribe(self, wav_path):
    """Transcribe wav_path. Respects legacy_inference lock for GPU coordination."""
    pcm = _load_pcm_from_wav(wav_path)      # helper: scipy.io.wavfile → float32
    result = self._asr_provider.transcribe(pcm, language=None)
    return _apply_engine_guards(result)      # no-speech filter, alpha filter, language steering
```

`type_text()` is updated to respect `TYPING_TOOL` config key, trying `ydotool` before `wtype` on Wayland (matching Handy's confirmed working setup).

### B. `voice_control.py` — Evening Review Wake-Words

```python
def _load_model(self):
    """Load ASR for wake-word detection. Tries fast provider first; falls back to tiny Whisper."""
    if self._provider is not None:
        return
    try:
        from audio_to_idea.asr import factory
        self._provider = factory.from_wake_word_config()
        self._provider.load()
    except Exception as exc:
        # Fail gracefully — wake-word detection is optional
        review_engine._rlog(f"voice_control: new provider failed ({exc}), using legacy tiny Whisper")
        from faster_whisper import WhisperModel
        self._provider = _LegacyWhisperAdapter(WhisperModel("tiny", device="cpu", compute_type="int8"))
```

No circular import risk: `voice_control.py` → `audio_to_idea.asr.factory` (no import of `review_engine` or `engine.py`).

### C. `audio_to_idea/transcription.py` — Batch Processor

```python
class Transcriber:
    def __init__(self, settings, model_info, cancel=None, notify=None):
        ...
        self._provider = None

    def _load(self):
        if self._provider is not None:
            return
        from audio_to_idea.asr import factory
        self._provider = factory.from_settings(self.settings)
        self._provider.load()

    def transcribe(self, path, chunk, glossary=''):
        check_cancel(self.cancel)
        audio = samples(path, chunk)
        if not audio.any():
            return {'index': chunk.index, 'start': chunk.start, 'end': chunk.end,
                    'segments': [], 'language': None}
        with inference(self.cancel, batch=True,
                       policy='queue' if self.settings['jobs']['gpu_busy_policy'] == 'cpu' else
                              self.settings['jobs']['gpu_busy_policy'],
                       notify=self.notify):
            self._load()
            result = self._provider.transcribe(audio, prompt=glossary[:2000] or None)
        # Convert ASRResult → existing chunk dict shape (merging.py/jobs.py unchanged)
        return _asr_result_to_chunk_dict(result, chunk, self._provider)

    def close(self):
        if self._provider:
            self._provider.close()
            self._provider = None
        gc.collect()
```

`jobs.py`, `merging.py`, `synthesis.py` — **zero changes**.

---

## 9. Post-Processing Layer (Handy-inspired)

### A. Filler word removal (`audio_to_idea/asr/filler_filter.py`)
Two-tier matching Handy's design:
- **Universal tier** (always applied): `hmm`, `hm`, `uhh`, `uh-huh` — language-independent fillers.
- **Language-gated tier** (applied only when language confirmed): English (`um`, `uh`, `like`, `you know`, `basically`), Hindi (`हाँ हाँ`, filler `तो` at start, `मतलब`).

### B. Custom word correction (`audio_to_idea/asr/word_corrector.py`)
- N-gram fuzzy matching using `rapidfuzz.fuzz.jaro_winkler_similarity`.
- Configurable threshold (default `0.18`, matching Handy's `word_correction_threshold`).
- Domain profiles in `audio_to_idea` can include `custom_words` lists (e.g., `["RoW", "DPR", "BOQ"]` for road infrastructure).

### C. VAD-guided chunking (`audio_to_idea/asr/vad_chunker.py`)
- Optional alternative to fixed-window chunking in `audio_to_idea/audio.py`.
- Cut points placed in middle of pauses (ported from Handy `chunking.rs`).
- Target: 30 s chunks, max: 40 s, min: 5 s — same as Handy's Silero defaults.
- Falls back to existing fixed chunker if VAD unavailable.

---

## 10. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| `transcribe-cpp` wheel fails on Ubuntu 22.04 (office) | High | Automatic fallback chain: `HandyCli → FasterWhisper`. `is_available()` catches `ImportError` cleanly. |
| `/usr/bin/handy` not installed on office PC | Medium | `HandyCliProvider.is_available()` returns `False`; silently skipped in fallback chain. |
| GGML Whisper `.bin` (Apex Hinglish) untested in `transcribe-cpp` 0.4.0 | Medium | Must test before closing Phase 4. Whisper `.bin` format is documented in transcribe.cpp; risk is low but unverified. |
| Nemotron produces no word timestamps | Low (refiner); Medium (SRT export) | Proportional estimation for `txt`/`json`. GUI shows warning on SRT/VTT export with Nemotron. Document limitation. |
| `validate()` change breaks existing `audio_to_idea_config.json` on save | Low | Additive change only; existing `faster-whisper` value still accepted. |
| Python 3.10 `str | None` syntax in type hints | High | `from __future__ import annotations` at top of every new file. |
| `isinstance(x, str | None)` on Python 3.10 fails | High | Use `isinstance(x, (str, type(None)))` or `x is None or isinstance(x, str)` throughout. |
| Voxtral 26 s cold load used accidentally in live dictation | Medium | Factory refuses Voxtral for `from_engine_config()` / `from_wake_word_config()` unless explicitly overridden. Config UI shows "batch only" badge. |
| `release_asr_before_synthesis` wastes time with Nemotron | Medium | When `backend == "transcribe-cpp"`, factory sets `settings['jobs']['release_asr_before_synthesis'] = False` in the settings copy it operates on (not persisted). |
| `voice_control.py` and `engine.py` both load models simultaneously | Low | `legacy_inference` lock in `resources.py` serialises GPU access. Wake-word listener only calls `transcribe()` when narration is playing (not during dictation). |

---

## 11. Non-Goals (explicitly out of scope)

- Speaker diarization (future milestone, per original spec).
- Real-time streaming / partial transcript preview during recording.
- Cloud ASR backends (OpenAI API, Azure, Google).
- Windows or macOS support.
- Changing Obsidian note format, evening review steps, or LLM prompt templates.
- Modifying `review_engine.py`, `review_dashboard.py`, `morning_brief.py`.
