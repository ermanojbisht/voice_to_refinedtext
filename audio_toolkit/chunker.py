"""Pause-Guided Long Audio Chunker.

Divides multi-minute audio recordings strictly at acoustic breath pauses (>250ms silence)
to eliminate Whisper hallucinations and avoid cutting words in half.
"""
from dataclasses import dataclass
from typing import List, Union, Optional
import os
import numpy as np

from .silero_vad import SileroVAD


@dataclass
class AudioChunk:
    index: int
    start_s: float
    end_s: float
    duration_s: float
    pcm: np.ndarray

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start_s": round(self.start_s, 2),
            "end_s": round(self.end_s, 2),
            "duration_s": round(self.duration_s, 2),
            "samples": len(self.pcm),
        }


class PauseGuidedChunker:
    """Intelligently slices long audio into 20-35s chunks aligned with natural breath pauses."""

    def __init__(
        self,
        target_chunk_s: float = 30.0,
        min_chunk_s: float = 8.0,
        max_chunk_s: float = 40.0,
        min_pause_ms: int = 250,
        sample_rate: int = 16000,
        vad: Optional[SileroVAD] = None,
    ):
        self.target_chunk_s = target_chunk_s
        self.min_chunk_s = min_chunk_s
        self.max_chunk_s = max_chunk_s
        self.min_pause_ms = min_pause_ms
        self.sample_rate = sample_rate
        self.vad = vad or SileroVAD.get_instance()

    def chunk_audio(
        self,
        audio_input: Union[str, np.ndarray],
    ) -> List[AudioChunk]:
        """Splits an audio file or PCM array into pause-aligned chunks.

        Returns:
            List[AudioChunk]
        """
        # Load audio into 16kHz float32 mono
        if isinstance(audio_input, str):
            if not os.path.isfile(audio_input):
                raise FileNotFoundError(f"Audio file not found: {audio_input}")
            import scipy.io.wavfile as wav
            import scipy.signal as signal
            sr, data = wav.read(audio_input)
            if data.dtype == np.int16:
                pcm = data.astype(np.float32) / 32768.0
            else:
                pcm = data.astype(np.float32)
            if len(pcm.shape) > 1:
                pcm = pcm.mean(axis=1)
            if sr != self.sample_rate and len(pcm) > 0:
                pcm = signal.resample(pcm, int(len(pcm) * self.sample_rate / sr))
        else:
            pcm = np.asarray(audio_input, dtype=np.float32)
            if len(pcm.shape) > 1:
                pcm = pcm.mean(axis=1)

        total_samples = len(pcm)
        total_duration_s = total_samples / self.sample_rate

        # Short audio fits entirely in one chunk
        if total_duration_s <= self.max_chunk_s:
            return [
                AudioChunk(
                    index=0,
                    start_s=0.0,
                    end_s=total_duration_s,
                    duration_s=total_duration_s,
                    pcm=pcm,
                )
            ]

        # 1. Compute speech timestamps via Silero VAD
        segments = self.vad.get_speech_timestamps(
            pcm,
            sample_rate=self.sample_rate,
            min_speech_duration_ms=250,
            min_silence_duration_ms=self.min_pause_ms,
        )

        # 2. Extract silence pause split candidates (midpoints of silence gaps >= min_pause_ms)
        min_pause_samples = int((self.min_pause_ms / 1000.0) * self.sample_rate)
        pause_cut_points = []

        if segments:
            for i in range(len(segments) - 1):
                gap_start = segments[i]["end"]
                gap_end = segments[i + 1]["start"]
                if gap_end - gap_start >= min_pause_samples:
                    # Choose silence midpoint
                    mid = (gap_start + gap_end) // 2
                    pause_cut_points.append(mid)

        # 3. Walk through audio and choose cuts near target_chunk_s
        chunks: List[AudioChunk] = []
        curr_start = 0
        chunk_idx = 0

        target_samples = int(self.target_chunk_s * self.sample_rate)
        min_samples = int(self.min_chunk_s * self.sample_rate)
        max_samples = int(self.max_chunk_s * self.sample_rate)

        while curr_start < total_samples:
            remaining = total_samples - curr_start
            if remaining <= max_samples:
                # Last remaining piece fits in one chunk
                chunk_pcm = pcm[curr_start:total_samples]
                chunks.append(
                    AudioChunk(
                        index=chunk_idx,
                        start_s=curr_start / self.sample_rate,
                        end_s=total_samples / self.sample_rate,
                        duration_s=len(chunk_pcm) / self.sample_rate,
                        pcm=chunk_pcm,
                    )
                )
                break

            ideal_cut = curr_start + target_samples
            min_allowed_cut = curr_start + min_samples
            max_allowed_cut = curr_start + max_samples

            # Find candidates in [min_allowed_cut, max_allowed_cut]
            candidates = [
                p for p in pause_cut_points
                if min_allowed_cut <= p <= max_allowed_cut
            ]

            if candidates:
                # Pick the pause cut closest to ideal_cut
                best_cut = min(candidates, key=lambda p: abs(p - ideal_cut))
            else:
                # Fallback: scan a 100ms window for the minimum energy point in [ideal_cut - 3s, ideal_cut + 3s]
                search_start = max(min_allowed_cut, ideal_cut - int(3.0 * self.sample_rate))
                search_end = min(max_allowed_cut, ideal_cut + int(3.0 * self.sample_rate))
                
                win_len = int(0.100 * self.sample_rate)  # 100ms
                min_energy = float("inf")
                best_cut = ideal_cut

                for p in range(search_start, search_end - win_len, win_len):
                    energy = float(np.sum(pcm[p : p + win_len] ** 2))
                    if energy < min_energy:
                        min_energy = energy
                        best_cut = p + (win_len // 2)

            chunk_pcm = pcm[curr_start:best_cut]
            chunks.append(
                AudioChunk(
                    index=chunk_idx,
                    start_s=curr_start / self.sample_rate,
                    end_s=best_cut / self.sample_rate,
                    duration_s=len(chunk_pcm) / self.sample_rate,
                    pcm=chunk_pcm,
                )
            )
            curr_start = best_cut
            chunk_idx += 1

        return chunks
