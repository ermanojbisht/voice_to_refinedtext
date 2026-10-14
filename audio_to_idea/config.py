"""Versioned configuration with explicit precedence and path provenance.

CLI overrides never save settings. GUI saves touch only the module's JSON file.
All relative file-config paths resolve from that file, not the caller's cwd.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse

from .schemas import AudioToIdeaError
from .storage import read_json, write_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = {
    'version': 1, 'integration': {'enabled': False},
    'ui': {'appearance': 'system'},
    'asr': {'backend': 'faster-whisper', 'model_id': 'Systran/faster-whisper-large-v3',
            'model_path': None, 'cache_root': None, 'revision': None, 'device': 'auto',
            'compute_type': 'auto', 'cpu_threads': 4, 'language': 'auto',
            'word_timestamps': True, 'offline': True, 'allow_downloads': False},
    'audio': {'sample_rate': 16000, 'normalize': False, 'target_lufs': -20.0,
              'true_peak_db': -2.0, 'chunk_seconds': 60.0, 'overlap_seconds': 1.5},
    'synthesis': {'backend': 'ollama', 'host': 'http://localhost:11434', 'model': None,
                  'temperature': .1, 'timeout_seconds': 300, 'context_tokens': 8192,
                  'output_language': 'source', 'context_profile': None,
                  'mode': 'clean_paragraph', 'prompt_directory': None, 'prompt_file': None},
    'output': {'directory': None, 'formats': ['txt'], 'save_metadata': True, 'overwrite': False},
    'jobs': {'workers': 1, 'gpu_busy_policy': 'queue', 'release_asr_before_synthesis': True},
    'watch': {'poll_seconds': 2.0, 'stable_seconds': 5.0, 'recursive': False},
}
ENV_FIELDS = {
    'AUDIO2IDEA_MODEL_PATH': 'asr.model_path', 'ASR_MODEL_PATH': 'asr.model_path',
    'AUDIO2IDEA_MODEL_ID': 'asr.model_id', 'AUDIO2IDEA_CACHE_ROOT': 'asr.cache_root',
    'AUDIO2IDEA_REVISION': 'asr.revision', 'AUDIO2IDEA_DEVICE': 'asr.device',
    'AUDIO2IDEA_COMPUTE_TYPE': 'asr.compute_type', 'AUDIO2IDEA_OLLAMA_HOST': 'synthesis.host',
    'AUDIO2IDEA_OLLAMA_MODEL': 'synthesis.model',
    'AUDIO2IDEA_MODE': 'synthesis.mode', 'AUDIO2IDEA_PROMPT_FILE': 'synthesis.prompt_file',
}
PATH_FIELDS = {'asr.model_path', 'asr.cache_root', 'output.directory', 'synthesis.context_profile',
               'synthesis.prompt_directory', 'synthesis.prompt_file'}


def default_config_path():
    base = ROOT if (ROOT / 'config.json').exists() else Path.cwd()
    return base / 'audio_to_idea_config.json'


def model_alias(value):
    if value in {'tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en', 'medium', 'medium.en', 'large-v2', 'large-v3'}:
        return f'Systran/faster-whisper-{value}'
    if value in {'turbo', 'large-v3-turbo'}:
        return 'mobiuslabsgmbh/faster-whisper-large-v3-turbo'
    return value


@dataclass
class Settings:
    data: dict
    path: Path
    sources: dict


def _path(value, base, environ):
    # Expand only documented $VAR forms; an unresolved variable is a useful error.
    def replace(match):
        name = match.group(1) or match.group(2)
        if name not in environ:
            raise AudioToIdeaError(f'Path references unset environment variable {name}')
        return environ[name]
    text = re.sub(r'\$\{([^}]+)\}|\$(\w+)', replace, str(value))
    path = Path(text).expanduser()
    return str((path if path.is_absolute() else base / path).resolve())


def load_settings(path=None, overrides=None, environ=None, legacy_path=None):
    env = os.environ if environ is None else environ
    explicit = path or env.get('AUDIO2IDEA_CONFIG')
    selected = Path(_path(explicit, Path.cwd(), env)) if explicit else default_config_path()
    if explicit and not selected.is_file():
        raise AudioToIdeaError(f'Configuration file does not exist: {selected}')
    data, sources = deepcopy(DEFAULTS), {}

    def apply(values, source, base):
        for dotted, value in values.items():
            section, key = dotted.split('.', 1)
            if dotted in PATH_FIELDS and value:
                value = _path(value, base, env)
            data.setdefault(section, {})[key] = value
            sources[dotted] = source

    legacy_file = Path(legacy_path or ROOT / 'config.json')
    try:
        legacy = read_json(legacy_file, {})
    except AudioToIdeaError:
        legacy = {}
        sources['legacy'] = 'invalid legacy config ignored; module settings are independent'
    if not isinstance(legacy, dict):
        legacy = {}
    fallbacks = {}
    if isinstance(legacy.get('WHISPER_MODEL'), str) and legacy['WHISPER_MODEL']:
        name = legacy['WHISPER_MODEL']
        key = 'asr.model_path' if Path(name).is_dir() else 'asr.model_id'
        fallbacks[key] = model_alias(name)
    if isinstance(legacy.get('OLLAMA_HOST'), str) and legacy['OLLAMA_HOST']:
        fallbacks['synthesis.host'] = legacy['OLLAMA_HOST']
    if isinstance(legacy.get('OLLAMA_MODELS'), dict) and isinstance(legacy['OLLAMA_MODELS'].get('en'), str):
        fallbacks['synthesis.model'] = legacy['OLLAMA_MODELS']['en']
    apply(fallbacks, 'legacy (read only)', legacy_file.resolve().parent)
    raw = read_json(selected, {})
    if not isinstance(raw, dict) or raw.get('version', 1) != 1:
        raise AudioToIdeaError('Settings must be a JSON object with version 1.')
    for key, value in raw.items():
        if key == 'version':
            data[key] = value
        elif isinstance(value, dict):
            apply({f'{key}.{k}': v for k, v in value.items()
                   if not (key == 'synthesis' and k == 'model' and v is None)}, 'config file', selected.parent)
        elif key in DEFAULTS:
            raise AudioToIdeaError(f'{key} must be an object.')
        else:
            data[key] = value  # Preserve extension keys when the GUI saves.
    if env.get('ASR_MODEL_PATH') and env.get('AUDIO2IDEA_MODEL_PATH') and env['ASR_MODEL_PATH'] != env['AUDIO2IDEA_MODEL_PATH']:
        raise AudioToIdeaError('ASR_MODEL_PATH and AUDIO2IDEA_MODEL_PATH conflict.')
    apply({field: env[name] for name, field in ENV_FIELDS.items() if env.get(name)}, 'environment', Path.cwd())
    apply({k: v for k, v in (overrides or {}).items() if v is not None}, 'command line', Path.cwd())
    rank = {'default': 0, 'legacy (read only)': 1, 'config file': 2, 'environment': 3, 'command line': 4}
    path_rank = rank.get(sources.get('asr.model_path', 'default'), 0)
    if any(rank.get(sources.get(key, 'default'), 0) > path_rank
           for key in ['asr.model_id', 'asr.cache_root', 'asr.revision']):
        # A CLI/environment selection must override a lower-priority GUI path.
        # At equal precedence a direct model folder still wins repository lookup.
        data['asr']['model_path'] = None
    data['asr']['model_id'] = model_alias(data['asr']['model_id'])
    validate(data)
    return Settings(data, selected, sources)


def validate(data):
    """Reject invalid explicit choices before probing hardware or writing files."""
    try:
        if data['version'] != 1:
            raise ValueError('Only settings version 1 is supported')
        if data.get('ui', {}).get('appearance', 'system') not in {'system', 'light', 'dark'}:
            raise ValueError('Appearance must be system, light or dark')
        a, p, s = data['asr'], data['audio'], data['synthesis']
        if s.get('mode', 'clean_paragraph') not in {'clean_paragraph', 'concise_summary', 'ideas_actions'}:
            raise ValueError('Processing mode must be clean_paragraph, concise_summary or ideas_actions')
        for key in ['prompt_directory', 'prompt_file']:
            if s.get(key) is not None and (not isinstance(s[key], str) or not s[key].strip()):
                raise ValueError(f'{key} must be a nonempty path or null')
        if a['backend'] != 'faster-whisper' or s['backend'] != 'ollama':
            raise ValueError('This release supports faster-whisper ASR and Ollama synthesis')
        if a['device'] not in {'auto', 'cpu', 'cuda'}:
            raise ValueError('ASR device must be auto, cpu or cuda; MPS needs another backend')
        if not isinstance(a['cpu_threads'], int) or isinstance(a['cpu_threads'], bool) or a['cpu_threads'] < 1:
            raise ValueError('CPU threads must be a positive whole number')
        if not isinstance(a['model_id'], str) or not a['model_id'].strip():
            raise ValueError('ASR model ID must be a nonempty string')
        if not isinstance(a['language'], str) or not a['language'].strip():
            raise ValueError('Language must be auto or an ASR language code')
        if p['sample_rate'] != 16000:
            raise ValueError('This backend requires a 16000 Hz preparation sample rate')
        if not 1 <= p['chunk_seconds'] <= 600 or not 0 <= p['overlap_seconds'] < p['chunk_seconds']:
            raise ValueError('Chunk duration must be 1–600 seconds; overlap must be smaller than the chunk')
        if not -70 <= p['target_lufs'] <= -5 or not -9 <= p['true_peak_db'] <= 0:
            raise ValueError('Normalization target/true peak is outside FFmpeg supported ranges')
        if not 0 <= s['temperature'] <= 2 or not 512 <= s['context_tokens'] <= 131072 or s['timeout_seconds'] <= 0:
            raise ValueError('Invalid synthesis temperature, context budget or timeout')
        if data['jobs']['workers'] != 1 or data['jobs']['gpu_busy_policy'] not in {'queue', 'error', 'cpu'}:
            raise ValueError('Use one worker and GPU policy queue, error or cpu')
        if data['watch']['poll_seconds'] <= 0 or data['watch']['stable_seconds'] < 1:
            raise ValueError('Watch polling must be positive; stable time must be at least one second')
        if not data['output']['formats'] or any(f not in {'txt', 'srt', 'vtt', 'json'} for f in data['output']['formats']):
            raise ValueError('Choose at least one transcript format: txt, srt, vtt, json')
        for dotted in ['integration.enabled', 'asr.word_timestamps', 'asr.offline', 'asr.allow_downloads',
                       'audio.normalize', 'output.save_metadata', 'output.overwrite',
                       'jobs.release_asr_before_synthesis', 'watch.recursive']:
            section, key = dotted.split('.')
            if not isinstance(data[section][key], bool):
                raise ValueError(f'{dotted} must be true or false')
        url = urlparse(s['host'])
        if url.scheme not in {'http', 'https'} or not url.hostname:
            raise ValueError('Ollama host must be an http(s) URL')
        if a['offline'] and url.hostname not in {'localhost', '127.0.0.1', '::1'}:
            raise ValueError('Offline mode requires Ollama on localhost; remote endpoints need offline=false')
        if a['offline'] and s['model'] and ':cloud' in str(s['model']).lower():
            raise ValueError('Cloud-hosted Ollama models cannot be used in offline mode')
        if a['offline'] and a['allow_downloads']:
            raise ValueError('Offline mode and allow_downloads=true conflict')
    except (KeyError, TypeError, ValueError) as exc:
        raise AudioToIdeaError(f'Invalid settings: {exc}') from exc


def save_settings(path, data):
    """Validate a whole settings draft, retaining extensions and legacy files."""
    validate(data)
    write_json(path, data)


def update_settings(path, changes, fallback=None):
    """Save only edited fields, without freezing environment/CLI overrides.

Read the file again so unrelated changes and unknown extension keys survive.
For a new GUI settings file, its initial snapshot supplies extension defaults.
Validation uses the full schema; a sparse existing file remains sparse on disk.
"""
    raw = read_json(path, deepcopy(fallback) if fallback is not None else {})
    if not isinstance(raw, dict) or raw.get('version', 1) != 1:
        raise AudioToIdeaError('Settings must be a JSON object with version 1.')
    for dotted, value in changes.items():
        section, key = dotted.split('.', 1)
        if not isinstance(raw.get(section, {}), dict):
            raise AudioToIdeaError(f'{section} must be an object.')
        raw.setdefault(section, {})[key] = value
    complete = deepcopy(DEFAULTS)
    for section, value in raw.items():
        if section in complete and isinstance(complete[section], dict) and isinstance(value, dict):
            complete[section].update(value)
        else:
            complete[section] = value
    validate(complete)
    write_json(path, raw)

