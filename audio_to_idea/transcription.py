"""Lazy local ASR. Each chunk result retains source-time segment/word data.

Supports:
- Faster-Whisper (CTranslate2)
- Transcribe-CPP (Nemotron GGUF, Whisper GGML, Voxtral GGUF)
- Handy-CLI (subprocess fallback)
"""
import gc

from .asr import ASRFactory
from .audio import samples
from .resources import inference
from .schemas import AudioToIdeaError, check_cancel


class Transcriber:
    def __init__(self, settings, model_info=None, cancel=None, notify=None):
        self.settings = settings
        self.model_info = model_info or {}
        self.cancel = cancel
        self.notify = notify
        self.provider = None

    def _load(self):
        if self.provider is not None:
            return

        asr = self.settings.get("asr", {})
        backend = asr.get("backend", "faster-whisper")

        try:
            # If explicit model_info with a resolved path was supplied for faster-whisper, use it
            if backend == "faster-whisper" and self.model_info.get("path"):
                from .asr.faster_whisper import FasterWhisperProvider
                self.provider = FasterWhisperProvider(
                    model_path_or_id=self.model_info["path"],
                    device=asr.get("device", "auto"),
                    compute_type=asr.get("compute_type", "auto"),
                    cpu_threads=asr.get("cpu_threads", 4),
                    word_timestamps=asr.get("word_timestamps", True),
                    offline=asr.get("offline", True),
                )
            else:
                self.provider = ASRFactory.from_settings(self.settings)

            self.provider.load()
        except Exception as exc:
            raise AudioToIdeaError(f"ASR load failed on {backend}: {exc}") from exc

    def transcribe(self, path, chunk, glossary=''):
        check_cancel(self.cancel)
        audio = samples(path, chunk)
        if not audio.any():
            return {'index': chunk.index, 'start': chunk.start, 'end': chunk.end, 'segments': [], 'language': None}

        policy = self.settings['jobs']['gpu_busy_policy']
        with inference(self.cancel, batch=True, policy='queue' if policy == 'cpu' else policy, notify=self.notify):
            self._load()
            asr = self.settings.get('asr', {})
            lang = None if asr.get('language', 'auto') == 'auto' else asr['language']

            result = self.provider.transcribe(
                audio,
                language=lang,
                prompt=glossary[:2000] if glossary else None,
            )

            segments = []
            for seg in result.segments:
                check_cancel(self.cancel)
                words = [
                    {
                        'text': w.text,
                        'start': chunk.start + w.start,
                        'end': chunk.start + w.end,
                        'probability': w.probability,
                    }
                    for w in seg.words
                ]
                segments.append({
                    'text': seg.text.strip(),
                    'start': chunk.start + seg.start,
                    'end': min(chunk.end, chunk.start + seg.end),
                    'words': words,
                    'avg_logprob': seg.avg_logprob,
                    'no_speech_prob': seg.no_speech_prob,
                })

        return {
            'index': chunk.index,
            'start': chunk.start,
            'end': chunk.end,
            'segments': segments,
            'language': result.language,
            'device': getattr(self.provider, 'active_device', None),
            'compute_type': getattr(self.provider, 'active_compute', None),
        }

    def close(self):
        """Release only this worker's weights before Ollama takes GPU memory."""
        if self.provider is not None:
            self.provider.close()
            self.provider = None
        gc.collect()
