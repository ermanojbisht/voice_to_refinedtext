#!/usr/bin/env python3
"""Voice wake-word control — keyword listener active during TTS narration.

Detects spoken keywords and triggers narration controls:
  "stop" / "रुको" / "ruko"      → stop_narration()
  "again" / "फिर से" / "replay"  → replay_narration(config)

Enabled via  "voice_control": true  in review_config.json (opt-in, default off).
An energy gate rejects low-level TTS speaker bleed picked up by the microphone.
The listener is idle when no narration is playing, so it adds zero overhead at rest.

Requires: faster-whisper (already in requirements.txt), sounddevice (ditto).
"""
import threading
import time
import sys
import numpy as np
import review_engine   # no circular import: review_engine does not import voice_control

_SAMPLE_RATE   = 16000
_CHUNK_SECONDS = 2
_CHUNK_SAMPLES = _CHUNK_SECONDS * _SAMPLE_RATE

# Keyword sets — substrings matched in lowercased transcript
_STOP_KEYWORDS   = {"stop", "रुको", "ruko", "रुक"}
_REPLAY_KEYWORDS = {"again", "replay", "फिर से", "phir se", "दोबारा", "dobara"}


class WakeWordListener:
    """Continuous keyword listener, active only while narration is playing."""

    def __init__(self):
        self._model    = None          # lazy-loaded WhisperModel("tiny")
        self._thread   = None
        self._stop_evt = threading.Event()

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self, threshold, is_narrating_fn, stop_fn, replay_fn):
        """Start the background listener.

        Args:
            threshold:       RMS energy gate (int16 scale, 0–32768).
            is_narrating_fn: Callable returning True while TTS is active.
            stop_fn:         Called when a stop keyword is detected.
            replay_fn:       Called when a replay keyword is detected.
        """
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(threshold, is_narrating_fn, stop_fn, replay_fn),
            daemon=True,
            name="wake-word-listener")
        self._thread.start()

    def stop(self):
        """Signal the listener thread to exit cleanly."""
        self._stop_evt.set()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel("tiny", device="cpu", compute_type="int8")

    def _run(self, threshold, is_narrating_fn, stop_fn, replay_fn):
        try:
            import sounddevice as sd
        except ImportError as exc:
            print(f"[voice_control] sounddevice not available — {exc}", file=sys.stderr)
            return

        try:
            self._load_model()
        except Exception as exc:
            review_engine._rlog(f"voice_control: model load failed — {exc}")
            return

        review_engine._rlog(
            f"voice_control: listener ready "
            f"(threshold={threshold}, chunk={_CHUNK_SECONDS}s)")

        while not self._stop_evt.is_set():
            # Idle when nothing is being narrated — zero CPU cost
            if not is_narrating_fn():
                time.sleep(0.2)
                continue

            try:
                audio = sd.rec(_CHUNK_SAMPLES, samplerate=_SAMPLE_RATE,
                               channels=1, dtype="float32")
                sd.wait()
                audio = audio.flatten()
            except Exception as exc:
                review_engine._rlog(f"voice_control: record error — {exc}")
                time.sleep(0.5)
                continue

            # Energy gate: TTS speaker bleed is typically quieter than direct speech.
            # Scale float32 RMS to int16 range (0–32768) to match SILENCE_THRESHOLD units.
            rms = int(np.sqrt(np.mean(audio ** 2)) * 32768)
            if rms < threshold:
                continue

            try:
                segments, _ = self._model.transcribe(
                    audio,
                    language=None,   # auto-detect; handles both Hindi and English
                    beam_size=1,
                    best_of=1,
                    vad_filter=True)
                text = " ".join(s.text.strip() for s in segments).lower().strip()
            except Exception as exc:
                review_engine._rlog(f"voice_control: transcribe error — {exc}")
                continue

            if not text:
                continue

            review_engine._rlog(f"voice_control: heard '{text}'")

            if any(kw in text for kw in _STOP_KEYWORDS):
                review_engine._rlog("voice_control: STOP triggered")
                stop_fn()
            elif any(kw in text for kw in _REPLAY_KEYWORDS):
                review_engine._rlog("voice_control: REPLAY triggered")
                replay_fn()

        review_engine._rlog("voice_control: listener stopped")
