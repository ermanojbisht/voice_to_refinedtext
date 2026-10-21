"""Piper Neural TTS Backend."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Mapping

from pwd_helper.tts.backends.base import BaseTTSBackend

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class PiperBackend(BaseTTSBackend):
    name = "piper"

    def __init__(self) -> None:
        self._piper_exe: str | None = None
        self._checked_availability: bool | None = None

    def _resolve_executable(self) -> str | None:
        if self._piper_exe and os.path.isfile(self._piper_exe):
            return self._piper_exe

        candidates = [
            os.path.join(os.path.dirname(sys.executable), "piper"),
            shutil.which("piper"),
            os.path.expanduser("~/.local/bin/piper"),
            os.path.expanduser("~/.cargo/bin/piper"),
            "/usr/local/bin/piper",
            "/usr/bin/piper",
        ]
        for c in candidates:
            if c and os.path.isfile(c) and os.access(c, os.X_OK):
                # Verify that running piper actually works (not a broken python script)
                try:
                    res = subprocess.run([c, "-h"], capture_output=True, timeout=3)
                    if res.returncode == 0:
                        self._piper_exe = c
                        return c
                except Exception:
                    continue
        return None

    def is_available(self) -> bool:
        if self._checked_availability is not None:
            return self._checked_availability
        exe = self._resolve_executable()
        self._checked_availability = (exe is not None)
        return self._checked_availability

    def synthesize_and_play(
        self,
        text: str,
        lang: str = "auto",
        blocking: bool = False,
        speed: float = 1.0,
        config: Mapping[str, Any] | None = None,
    ) -> bool:
        exe = self._resolve_executable()
        if not exe:
            return False

        cfg = config or {}
        is_hindi = (lang == "hi") or any("\u0900" <= ch <= "\u097F" for ch in text)

        if is_hindi:
            rel_model = cfg.get("piper_model_hi", "models/hi_IN-priyamvada-medium.onnx")
        else:
            rel_model = cfg.get("piper_model", "models/en_US-ryan-high.onnx")

        model_path = os.path.expanduser(str(rel_model))
        if not os.path.isabs(model_path):
            model_path = str(_REPO_ROOT / model_path)

        if not os.path.isfile(model_path):
            return False

        paplay = shutil.which("paplay") or shutil.which("aplay")
        if not paplay:
            return False

        tmp_path = tempfile.mktemp(suffix=".wav")
        try:
            synth_cmd = [exe, "--model", model_path, "--output_file", tmp_path]
            if speed != 1.0:
                # Piper supports --length-scale (inverse of speed)
                synth_cmd.extend(["--length-scale", str(round(1.0 / speed, 2))])

            synth = subprocess.Popen(
                synth_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            synth.communicate(input=text.encode("utf-8"), timeout=15)
            if synth.returncode != 0 or not os.path.isfile(tmp_path):
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
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            return False
