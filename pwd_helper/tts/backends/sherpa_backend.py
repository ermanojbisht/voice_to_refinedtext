"""Sherpa-ONNX Backend — Fast Kokoro-82M & VITS CPU Synthesis."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Mapping

from pwd_helper.tts.backends.base import BaseTTSBackend

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class SherpaBackend(BaseTTSBackend):
    name = "sherpa"

    def __init__(self) -> None:
        self._tts_instance = None
        self._loaded_model_dir: str | None = None

    def _find_model_dir(self, config: Mapping[str, Any] | None = None) -> Path | None:
        cfg = config or {}
        custom_dir = cfg.get("sherpa_model_dir")
        if custom_dir:
            p = Path(custom_dir).expanduser()
            if p.is_dir():
                return p

        # Check default paths in models/
        candidates = [
            _REPO_ROOT / "models" / "kokoro-en-v0_19",
            _REPO_ROOT / "models" / "kokoro",
            _REPO_ROOT / "models" / "vits-piper-en_US-ryan-high",
            Path.home() / ".cache" / "sherpa-onnx" / "kokoro-en-v0_19",
        ]
        for c in candidates:
            if c.is_dir() and any(c.glob("*.onnx")):
                return c
        return None

    def is_available(self) -> bool:
        try:
            import sherpa_onnx
            # Available if sherpa_onnx is installed and a supported model directory exists
            return self._find_model_dir() is not None
        except ImportError:
            return False

    def synthesize_and_play(
        self,
        text: str,
        lang: str = "auto",
        blocking: bool = False,
        speed: float = 1.0,
        config: Mapping[str, Any] | None = None,
    ) -> bool:
        try:
            import sherpa_onnx
            import soundfile as sf
        except ImportError:
            return False

        model_dir = self._find_model_dir(config)
        if not model_dir:
            return False

        try:
            # Check for kokoro
            kokoro_model = next(model_dir.glob("model*.onnx"), None)
            voices = next(model_dir.glob("voices.bin"), None)
            tokens = next(model_dir.glob("tokens.txt"), None)
            data_dir = model_dir / "espeak-ng-data"

            if not kokoro_model or not tokens or not data_dir.is_dir():
                return False

            tts_config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                        model=str(kokoro_model),
                        voices=str(voices) if voices else "",
                        tokens=str(tokens),
                        data_dir=str(data_dir),
                        length_scale=round(1.0 / speed, 2),
                    ),
                    num_threads=2,
                    debug=False,
                )
            )

            tts = sherpa_onnx.OfflineTts(tts_config)
            audio = tts.generate(text, sid=0, speed=speed)
            if not audio or len(audio.samples) == 0:
                return False

            tmp_path = tempfile.mktemp(suffix=".wav")
            sf.write(tmp_path, audio.samples, audio.sample_rate)

            paplay = shutil.which("paplay") or shutil.which("aplay")
            if not paplay:
                return False

            play = subprocess.Popen([paplay, tmp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            from pwd_helper.tts.dispatcher import get_dispatcher
            get_dispatcher().set_active_proc(play)

            if blocking:
                play.wait()

            def _cleanup():
                try:
                    play.wait()
                finally:
                    if os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass

            threading.Thread(target=_cleanup, daemon=True).start()
            return True
        except Exception:
            return False
