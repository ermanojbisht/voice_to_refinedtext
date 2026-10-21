"""eSpeak-NG Backend — Universal offline safety fallback."""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Mapping

from pwd_helper.tts.backends.base import BaseTTSBackend


class ESpeakBackend(BaseTTSBackend):
    name = "espeak"

    def __init__(self) -> None:
        self._voice_cache: str | None = None

    def is_available(self) -> bool:
        return shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None

    def _best_voice(self) -> str:
        if self._voice_cache:
            return self._voice_cache
        mbrola_paths = [
            ("/usr/share/mbrola/us2/us2", "mb-us2"),
            ("/usr/share/mbrola/us1/us1", "mb-us1"),
            ("/usr/share/mbrola/en1/en1", "mb-en1"),
        ]
        for data_file, voice_id in mbrola_paths:
            if os.path.exists(data_file):
                self._voice_cache = voice_id
                return voice_id
        self._voice_cache = "en-us"
        return "en-us"

    def synthesize_and_play(
        self,
        text: str,
        lang: str = "auto",
        blocking: bool = False,
        speed: float = 1.0,
        config: Mapping[str, Any] | None = None,
    ) -> bool:
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if not exe:
            return False

        is_hindi = (lang == "hi") or any("\u0900" <= ch <= "\u097F" for ch in text)
        base_rate = 135
        calc_rate = str(int(base_rate * speed))

        if is_hindi:
            cmd = [exe, "-v", "hi", "-s", calc_rate, "-a", "90", text]
        else:
            voice = self._best_voice()
            if voice.startswith("mb-"):
                cmd = [exe, "-v", voice, "-s", str(int(145 * speed)), "-a", "90", text]
            else:
                cmd = [exe, "-v", voice, "-s", calc_rate, "-p", "38", "-g", "3", "-a", "90", text]

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Track PID in dispatcher via active proc if available
            from pwd_helper.tts.dispatcher import get_dispatcher
            get_dispatcher().set_active_proc(proc)

            if blocking:
                proc.wait()
            return True
        except Exception:
            return False
