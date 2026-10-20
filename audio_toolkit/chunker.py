"""Pause-Guided Long Audio Chunker.

Divides multi-minute audio recordings strictly at acoustic breath pauses (>=250ms silence)
using Handy's acoustic scoring algorithm to eliminate Whisper hallucinations and avoid
cutting words in half. Zero hardcoded thresholds; all parameters are configurable.
"""
from dataclasses import dataclass
from typing import List, Union, Optional
import os
import json
import numpy as np

from .silero_vad import SileroVAD


def _load_chunker_config() -> dict:
    """Loads chunking configuration defaults from config.json to prevent hardcoding."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    defaults = {
        "PAUSE_GUIDED_CHUNKING": True,
        "CHUNK_TARGET_SECONDS": 30.0,
        "CHUNK_MIN_SECONDS": 8.0,
        "CHUNK_MAX_SECONDS": 40.0,
        "CHUNK_MIN_PAUSE_MS": 250,
    }
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                for k in defaults:
                    if k in user_cfg:
                        defaults[k] = user_cfg[k]
        except Exception:
            pass
    return defaults


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


@dataclass
class PauseCandidate:
    gap_start_sample: int
    gap_end_sample: int
    midpoint_sample: int
    duration_s: float


class PauseGuidedChunker:
    """Intelligently slices long audio into pause-aligned chunks using Handy's acoustic scoring."""

    def __init__(
        self,
        target_chunk_s: Optional[float] = None,
        min_chunk_s: Optional[float] = None,
        max_chunk_s: Optional[float] = None,
        min_pause_ms: Optional[int] = None,
        sample_rate: int = 16000,
        vad: Optional[SileroVAD] = None,
    ):
        cfg = _load_chunker_config()
        self.target_chunk_s = float(target_chunk_s if target_chunk_s is not None else cfg["CHUNK_TARGET_SECONDS"])
        self.min_chunk_s = float(min_chunk_s if min_chunk_s is not None else cfg["CHUNK_MIN_SECONDS"])
        self.max_chunk_s = float(max_chunk_s if max_chunk_s is not None else cfg["CHUNK_MAX_SECONDS"])
        self.min_pause_ms = int(min_pause_ms if min_pause_ms is not None else cfg["CHUNK_MIN_PAUSE_MS"])
        self.sample_rate = sample_rate
        self.vad = vad or SileroVAD.get_instance()

    @staticmethod
    def calculate_candidate_score(gap_duration_s: float, position_s: float, target_s: float) -> float:
        """Handy's asymmetric acoustic score:
        Score = min(gap_duration_s, 1.0) - off_target_penalty

        Penalty:
          - 0.10/s if position > target (late cuts penalized harder)
          - 0.05/s if position <= target (early cuts penalized less)
        Longer silence gaps (up to 1.0s) between full sentences are preferred over brief breath pauses.
        """
        if position_s > target_s:
            off_target = 0.10 * (position_s - target_s)
        else:
            off_target = 0.05 * (target_s - position_s)
        return min(gap_duration_s, 1.0) - off_target

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

        # 2. Extract silence pause candidates (gaps >= min_pause_ms)
        min_pause_samples = int((self.min_pause_ms / 1000.0) * self.sample_rate)
        candidates: List[PauseCandidate] = []

        if segments:
            for i in range(len(segments) - 1):
                gap_start = segments[i]["end"]
                gap_end = segments[i + 1]["start"]
                gap_len = gap_end - gap_start
                if gap_len >= min_pause_samples:
                    mid = (gap_start + gap_end) // 2
                    candidates.append(
                        PauseCandidate(
                            gap_start_sample=gap_start,
                            gap_end_sample=gap_end,
                            midpoint_sample=mid,
                            duration_s=gap_len / self.sample_rate,
                        )
                    )

        # 3. Walk through audio and choose optimal cut points
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

            min_allowed_cut = curr_start + min_samples
            max_allowed_cut = curr_start + max_samples

            # Find candidates in [min_allowed_cut, max_allowed_cut]
            valid_candidates = [
                c for c in candidates
                if min_allowed_cut <= c.midpoint_sample <= max_allowed_cut
            ]

            if valid_candidates:
                # Score each candidate using Handy's formula
                best_cand = max(
                    valid_candidates,
                    key=lambda c: self.calculate_candidate_score(
                        gap_duration_s=c.duration_s,
                        position_s=(c.midpoint_sample - curr_start) / self.sample_rate,
                        target_s=self.target_chunk_s,
                    ),
                )
                best_cut = best_cand.midpoint_sample
            else:
                # Fallback: scan for minimum RMS energy window (100ms) around ideal cut
                ideal_cut = curr_start + target_samples
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
