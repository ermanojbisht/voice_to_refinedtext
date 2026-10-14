"""Cancellable local Ollama client; generation options belong in options."""
import json

from .resources import inference
from .schemas import AudioToIdeaError, check_cancel


class OllamaClient:
    def __init__(self, settings, cancel=None, notify=None):
        import requests
        self.settings, self.cancel, self.notify = settings, cancel, notify
        self.details = None
        self.session = requests.Session()
        # An environment proxy must not forward localhost speech to an external
        # endpoint when the user has explicitly selected offline processing.
        self.session.trust_env = not settings['asr']['offline']

    def close(self):
        self.session.close()

    def validate_runtime(self):
        """Check context capacity and remote-model metadata without inference."""
        import requests
        cfg = self.settings['synthesis']
        if self.details is None:
            try:
                response = self.session.post(cfg['host'].rstrip('/') + '/api/show', json={'model': cfg['model']}, timeout=5)
                response.raise_for_status()
                self.details = response.json()
            except (requests.RequestException, ValueError) as exc:
                raise AudioToIdeaError(f'Cannot inspect selected Ollama model: {exc}') from exc
        if not isinstance(self.details, dict) or not isinstance(self.details.get('model_info', {}), dict):
            raise AudioToIdeaError('Ollama returned invalid model metadata.')
        limits = [v for k, v in self.details.get('model_info', {}).items()
                  if k.endswith('.context_length') and isinstance(v, int)]
        if limits and cfg['context_tokens'] > min(limits):
            raise AudioToIdeaError(f'Context budget {cfg["context_tokens"]} exceeds this model’s capacity {min(limits)}.')
        if self.settings['asr']['offline'] and (self.details.get('remote_host') or self.details.get('remote_model')):
            raise AudioToIdeaError('Selected Ollama model uses a remote service; choose local weights for offline mode.')

    def generate(self, prompt, schema):
        import requests
        cfg = self.settings['synthesis']
        if not cfg['model']:
            raise AudioToIdeaError('Choose an Ollama synthesis model in settings or with --synthesis-model.')
        check_cancel(self.cancel)
        self.validate_runtime()
        payload = {'model': cfg['model'], 'prompt': prompt, 'stream': True, 'format': schema,
                   'think': False, 'options': {'temperature': cfg['temperature'], 'num_ctx': cfg['context_tokens'],
                                              'num_predict': min(4096, cfg['context_tokens'] // 4)}}
        try:
            policy = self.settings['jobs']['gpu_busy_policy']
            with inference(self.cancel, batch=True, policy='queue' if policy == 'cpu' else policy, notify=self.notify):
                with self.session.post(cfg['host'].rstrip('/') + '/api/generate', json=payload, stream=True,
                                   timeout=(5, cfg['timeout_seconds'])) as response:
                    response.raise_for_status()
                    pieces, finished = [], False
                    for line in response.iter_lines(chunk_size=128):
                        check_cancel(self.cancel)
                        if not line:
                            continue
                        part = json.loads(line)
                        if part.get('error'):
                            raise AudioToIdeaError(f'Ollama: {part["error"]}')
                        pieces.append(part.get('response', ''))
                        if part.get('done'):
                            if part.get('done_reason') == 'length':
                                raise AudioToIdeaError('Synthesis reached its token limit. Increase context budget or use smaller input sections.')
                            finished = True
                    if not finished:
                        raise AudioToIdeaError('Ollama disconnected before completing synthesis; transcript is preserved.')
            return json.loads(''.join(pieces))
        except (requests.RequestException, ValueError) as exc:
            raise AudioToIdeaError(f'Ollama synthesis failed: {exc}. Check host/model or retry ideas only.') from exc

    def readiness(self):
        import requests
        cfg = self.settings['synthesis']
        try:
            response = self.session.get(cfg['host'].rstrip('/') + '/api/tags', timeout=5)
            response.raise_for_status()
            names = [m['name'] for m in response.json()['models']]
            ready = cfg['model'] in names or (str(cfg['model']) + ':latest') in names
            if ready:
                self.validate_runtime()
            return {'models': names, 'selected': cfg['model'], 'ready': ready}
        except (requests.RequestException, ValueError, KeyError) as exc:
            raise AudioToIdeaError(f'Ollama is unavailable: {exc}') from exc

