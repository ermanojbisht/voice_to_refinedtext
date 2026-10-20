"""Handy CLI Subprocess provider for BaseASRProvider.

Provides zero-Python-dependency fallback by invoking the system-installed
/usr/bin/handy binary with headless `--transcribe-file <path> --json`.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base import ASRResult, ASRSegment, ASRWord, BaseASRProvider

if TYPE_CHECKING:
    import numpy as np


class HandyCliProvider(BaseASRProvider):
    """Subprocess ASR runner invoking `/usr/bin/handy`."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        *,
        handy_binary: Optional[str] = None,
    ):
        self.model_id = model_id
        self.binary_path = handy_binary or shutil.which("handy") or "/usr/bin/handy"

    def is_available(self) -> bool:
        return bool(self.binary_path and os.path.isfile(self.binary_path) and os.access(self.binary_path, os.X_OK))

    def load(self) -> None:
        """No-op: Handy CLI loads model on execution."""
        pass

    def transcribe(
        self,
        pcm: np.ndarray,
        *,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        wav_path: Optional[str] = None,
        **kwargs: Any
    ) -> ASRResult:
        if not self.is_available():
            raise RuntimeError(f"Handy binary not available at {self.binary_path}")

        t0 = time.perf_counter()
        duration_s = float(len(pcm)) / 16000.0 if len(pcm) > 0 else 0.0

        if len(pcm) == 0:
            return ASRResult(
                text="",
                language=language,
                duration=0.0,
                latency_ms=0.0,
                segments=[],
                backend="handy_cli",
                model_path=str(self.model_id or "default"),
            )

        # Write PCM to a temporary or provided WAV file
        temp_file = None
        if wav_path and os.path.isfile(wav_path):
            target_wav = wav_path
        else:
            import numpy as np
            import scipy.io.wavfile as wav_io

            fd, temp_file = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            # Ensure int16 for Handy
            int_pcm = (np.clip(pcm, -1.0, 1.0) * 32767.0).astype(np.int16)
            wav_io.write(temp_file, 16000, int_pcm)
            target_wav = temp_file

        cmd = [self.binary_path, "-f", target_wav, "--json"]
        if self.model_id:
            cmd.extend(["--model", self.model_id])

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
            stdout = proc.stdout.strip()

            text = ""
            best_ms = 0.0
            # Look for JSON line in output
            for line in stdout.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        text = data.get("text", "")
                        best_ms = float(data.get("best_ms", 0.0))
                        break
                    except Exception:
                        continue
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

        latency_ms = best_ms if best_ms > 0 else (time.perf_counter() - t0) * 1000.0

        segments: List[ASRSegment] = []
        if text:
            segments.append(
                ASRSegment(
                    id="S00001",
                    text=text,
                    start=0.0,
                    end=duration_s,
                    words=[],
                )
            )

        return ASRResult(
            text=text,
            language=language,
            duration=duration_s,
            latency_ms=latency_ms,
            segments=segments,
            backend="handy_cli",
            model_path=str(self.model_id or "default"),
        )

    def close(self) -> None:
        """No-op for subprocess provider."""
        pass
