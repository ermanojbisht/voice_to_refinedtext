"""Thread-safe circular audio buffer (pre-roll ring buffer) to eliminate speech onset truncation."""
import threading
import numpy as np


class CircularAudioBuffer:
    """Fixed-capacity circular FIFO audio buffer storing recent 16kHz mono float32 PCM samples."""

    def __init__(self, capacity_ms: int = 600, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.capacity_samples = int((capacity_ms / 1000.0) * sample_rate)
        self._buffer = np.zeros(self.capacity_samples, dtype=np.float32)
        self._write_pos = 0
        self._total_written = 0
        self._lock = threading.Lock()

    def write(self, data: np.ndarray) -> None:
        """Pushes raw PCM samples into the circular buffer. Accepts 1D float32 or int16."""
        if data is None or len(data) == 0:
            return

        if data.dtype == np.int16:
            samples = data.astype(np.float32) / 32768.0
        else:
            samples = data.astype(np.float32)

        if len(samples.shape) > 1:
            samples = samples.mean(axis=1)

        n = len(samples)
        if n == 0:
            return

        with self._lock:
            if n >= self.capacity_samples:
                # Chunk is larger than total buffer: take only the most recent capacity_samples
                self._buffer[:] = samples[-self.capacity_samples:]
                self._write_pos = 0
                self._total_written += n
                return

            # Compute slice boundaries
            end_pos = self._write_pos + n
            if end_pos <= self.capacity_samples:
                self._buffer[self._write_pos:end_pos] = samples
            else:
                first_part = self.capacity_samples - self._write_pos
                self._buffer[self._write_pos:] = samples[:first_part]
                second_part = n - first_part
                self._buffer[:second_part] = samples[first_part:]

            self._write_pos = (self._write_pos + n) % self.capacity_samples
            self._total_written += n

    def get_pre_roll(self, duration_ms: int = 500) -> np.ndarray:
        """Extracts the most recent `duration_ms` of audio as a contiguous 1D float32 array."""
        target_samples = min(int((duration_ms / 1000.0) * self.sample_rate), self.capacity_samples)
        with self._lock:
            if self._total_written == 0:
                return np.zeros(target_samples, dtype=np.float32)

            available = min(self._total_written, self.capacity_samples)
            actual_samples = min(target_samples, available)

            # Roll buffer so newest sample is at the end
            ordered = np.roll(self._buffer, -self._write_pos)
            if self._total_written < self.capacity_samples:
                # Buffer has not wrapped yet; valid samples are in [0 : self._total_written]
                valid = self._buffer[:self._total_written]
                return valid[-actual_samples:].copy()

            return ordered[-actual_samples:].copy()

    def clear(self) -> None:
        """Resets the buffer contents and write pointer."""
        with self._lock:
            self._buffer.fill(0.0)
            self._write_pos = 0
            self._total_written = 0

    @property
    def total_written(self) -> int:
        with self._lock:
            return self._total_written
