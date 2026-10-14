"""Lazy local ASR. Each chunk result retains source-time segment/word data."""
import gc

from .audio import samples
from .models import execution_device
from .resources import inference
from .schemas import AudioToIdeaError, check_cancel


class Transcriber:
    def __init__(self, settings, model_info, cancel=None, notify=None):
        self.settings, self.model_info = settings, model_info
        self.cancel, self.notify = cancel, notify
        self.model = None
        self.device = None
        self.compute = None

    def _load(self):
        if self.model is not None:
            return
        from faster_whisper import WhisperModel
        asr = self.settings['asr']
        device, compute = execution_device(asr)
        if self.settings['jobs']['gpu_busy_policy'] == 'cpu' and asr['device'] == 'auto':
            device, compute = execution_device({**asr, 'device': 'cpu', 'compute_type': 'auto'})
        try:
            self.model = WhisperModel(self.model_info['path'], device=device, compute_type=compute,
                                     cpu_threads=asr['cpu_threads'], local_files_only=True)
        except Exception as exc:
            # An explicitly selected GPU must never silently turn into CPU.
            if asr['device'] != 'auto' or device != 'cuda':
                raise AudioToIdeaError(f'ASR load failed on {device}: {exc}. Check model assets/runtime or choose CPU.') from exc
            if self.notify:
                self.notify({'stage': 'warning', 'message': f'CUDA load failed; using CPU: {exc}'})
            device, compute = execution_device({**asr, 'device': 'cpu', 'compute_type': 'auto'})
            self.model = WhisperModel(self.model_info['path'], device=device, compute_type=compute,
                                     cpu_threads=asr['cpu_threads'], local_files_only=True)
        self.device, self.compute = device, compute

    def transcribe(self, path, chunk, glossary=''):
        check_cancel(self.cancel)
        audio = samples(path, chunk)
        if not audio.any():
            return {'index': chunk.index, 'start': chunk.start, 'end': chunk.end, 'segments': [], 'language': None}
        policy = self.settings['jobs']['gpu_busy_policy']
        with inference(self.cancel, batch=True, policy='queue' if policy == 'cpu' else policy, notify=self.notify):
            self._load()
            asr = self.settings['asr']
            result, info = self.model.transcribe(audio, language=None if asr['language'] == 'auto' else asr['language'],
                                                multilingual=asr['language'] == 'auto', word_timestamps=asr['word_timestamps'],
                                                condition_on_previous_text=False, vad_filter=True,
                                                initial_prompt=glossary[:2000] or None)
            segments = []
            for seg in result:
                check_cancel(self.cancel)
                words = [{'text': w.word, 'start': chunk.start + w.start, 'end': chunk.start + w.end,
                          'probability': w.probability} for w in (seg.words or [])]
                segments.append({'text': seg.text.strip(), 'start': chunk.start + seg.start,
                                 'end': min(chunk.end, chunk.start + seg.end), 'words': words,
                                 'avg_logprob': seg.avg_logprob, 'no_speech_prob': seg.no_speech_prob})
        return {'index': chunk.index, 'start': chunk.start, 'end': chunk.end, 'segments': segments,
                'language': info.language, 'device': self.device, 'compute_type': self.compute}

    def close(self):
        """Release only this worker's weights before Ollama takes GPU memory."""
        self.model = None
        gc.collect()

