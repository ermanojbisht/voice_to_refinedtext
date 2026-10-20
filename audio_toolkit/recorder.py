"""Stream Recorder integrating pre-speech circular ring buffering and neural VAD."""
import os
import time
import threading
import subprocess
from typing import Optional, Callable
import numpy as np
import scipy.io.wavfile as wav

try:
    import sounddevice as sd
except ImportError:
    sd = None

from .ring_buffer import CircularAudioBuffer
from .silero_vad import SileroVAD


class StreamRecorder:
    """Microphone stream recorder with pre-roll ring buffer and Silero VAD auto-stop."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        pre_roll_ms: int = 500,
        silence_dur: float = 2.5,
        initial_silence_timeout: float = 6.0,
        vad_threshold: float = 0.50,
        rms_threshold: int = 300,
        script_dir: Optional[str] = None,
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.pre_roll_ms = pre_roll_ms
        self.silence_dur = silence_dur
        self.initial_silence_timeout = initial_silence_timeout
        self.vad_threshold = vad_threshold
        self.rms_threshold = rms_threshold
        self.script_dir = script_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.ring_buffer = CircularAudioBuffer(capacity_ms=max(600, pre_roll_ms + 100), sample_rate=sample_rate)
        self.vad = SileroVAD.get_instance()
        self.stop_event = threading.Event()
        self._bg_thread = None
        self._bg_stop = threading.Event()

    def start_background_listener(self) -> None:
        """Starts a low-overhead background thread keeping the pre-roll ring buffer full."""
        if self._bg_thread is not None and self._bg_thread.is_alive():
            return
        if sd is None:
            return

        self._bg_stop.clear()

        def _bg_worker():
            try:
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="int16",
                    blocksize=self.chunk_size,
                ) as stream:
                    while not self._bg_stop.is_set():
                        data, overflowed = stream.read(self.chunk_size)
                        if not overflowed and len(data) > 0:
                            self.ring_buffer.write(data)
            except Exception:
                pass

        self._bg_thread = threading.Thread(target=_bg_worker, daemon=True, name="AudioPreRollListener")
        self._bg_thread.start()

    def stop_background_listener(self) -> None:
        """Stops the background pre-roll thread."""
        self._bg_stop.set()
        if self._bg_thread is not None:
            self._bg_thread.join(timeout=1.0)
            self._bg_thread = None

    def stop_recording(self) -> None:
        """Signals active recording loop to finalize immediately."""
        self.stop_event.set()

    def record(
        self,
        output_wav: Optional[str] = None,
        on_start: Optional[Callable[[], None]] = None,
        on_end: Optional[Callable[[], None]] = None,
        pre_record_notification: Optional[str] = None,
        play_sounds: bool = True,
        max_duration_s: float = 300.0,
        on_audio_chunk: Optional[Callable[[np.ndarray, float], None]] = None,
    ) -> str:
        """Records speech with pre-roll audio prepending and neural VAD silence auto-stop.

        Returns:
            Absolute path to output WAV file.
        """
        if sd is None:
            raise RuntimeError("sounddevice is not installed or audio hardware is unavailable.")

        wav_path = output_wav or os.path.join(self.script_dir, "input.wav")
        self.stop_event.clear()

        # 1. Capture snapshot of pre-roll audio before active loop begins
        pre_roll_pcm = self.ring_buffer.get_pre_roll(duration_ms=self.pre_roll_ms)
        pre_roll_int16 = (np.clip(pre_roll_pcm, -1.0, 1.0) * 32767).astype(np.int16)

        # 2. Desktop notification if requested
        if pre_record_notification:
            try:
                subprocess.run(
                    ["notify-send", "-i", "dialog-information", "Voice Refiner", pre_record_notification],
                    timeout=3,
                    check=False,
                )
            except Exception:
                pass

        if on_start:
            on_start()

        # 3. Start audio sound effect
        if play_sounds:
            start_sound = os.path.join(self.script_dir, "sounds", "start.oga")
            if os.path.isfile(start_sound):
                subprocess.run(["paplay", start_sound], check=False)

        audio_buffer = []
        silent_chunks = 0
        has_spoken = False
        start_time = time.monotonic()

        # Temporary pause background listener to avoid double-reading audio stream
        was_bg_running = (self._bg_thread is not None and self._bg_thread.is_alive())
        if was_bg_running:
            self.stop_background_listener()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self.chunk_size,
            ) as stream:
                while not self.stop_event.is_set():
                    chunk, overflowed = stream.read(self.chunk_size)
                    audio_buffer.append(chunk)
                    self.ring_buffer.write(chunk)

                    energy = float(np.sqrt(np.mean(chunk.astype(float) ** 2)))
                    if on_audio_chunk:
                        try:
                            on_audio_chunk(chunk, energy)
                        except Exception:
                            pass

                    # Neural VAD evaluation
                    if self.vad.is_neural_available:
                        speech_prob = self.vad.speech_probability(chunk)
                        is_speech_now = speech_prob >= self.vad_threshold
                    else:
                        is_speech_now = energy >= self.rms_threshold

                    if is_speech_now:
                        has_spoken = True
                        silent_chunks = 0
                    else:
                        silent_chunks += 1
                        elapsed_silence = (silent_chunks * self.chunk_size) / self.sample_rate
                        if has_spoken:
                            if elapsed_silence >= self.silence_dur:
                                break
                        else:
                            if elapsed_silence >= self.initial_silence_timeout:
                                break

                    # Guard against runaway recording exceeding max_duration_s
                    if (time.monotonic() - start_time) >= max_duration_s:
                        break
        finally:
            if was_bg_running:
                self.start_background_listener()

        if play_sounds:
            end_sound = os.path.join(self.script_dir, "sounds", "end.oga")
            if os.path.isfile(end_sound):
                subprocess.run(["paplay", end_sound], check=False)

        if on_end:
            on_end()

        # Combine pre-roll + actively captured chunks
        if audio_buffer:
            active_audio = np.concatenate(audio_buffer)
            if pre_roll_int16 is not None and len(pre_roll_int16) > 0 and has_spoken:
                # Prepend pre-roll only if actual speech was captured
                final_audio = np.concatenate([pre_roll_int16.reshape(-1, 1), active_audio.reshape(-1, 1)])
            else:
                final_audio = active_audio
        elif pre_roll_int16 is not None and len(pre_roll_int16) > 0:
            final_audio = pre_roll_int16.reshape(-1, 1)
        else:
            final_audio = np.zeros((self.sample_rate, 1), dtype=np.int16)

        wav.write(wav_path, self.sample_rate, final_audio)
        return wav_path
