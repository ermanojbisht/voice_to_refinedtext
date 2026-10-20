"""Read-only model discovery: cache repositories are not model directories."""
import os
from pathlib import Path
import shutil

from .schemas import AudioToIdeaError
from .storage import read_json


def cache_root(asr):
    env = os.environ
    return Path(asr.get('cache_root') or env.get('HF_HUB_CACHE') or env.get('HUGGINGFACE_HUB_CACHE')
                or (Path(env.get('HF_HOME', Path.home() / '.cache/huggingface')) / 'hub')).expanduser()


def inspect_model(path):
    path = Path(path)
    # faster-whisper supplies feature-extractor defaults when preprocessor_config
    # is absent; older official tiny models legitimately omit that optional file.
    # Tokenizer/config/weights must be present to prevent hub fallback calls.
    missing = [n for n in ['model.bin', 'config.json', 'tokenizer.json']
               if not (path / n).is_file()]
    broken = sorted(p.name for p in path.iterdir() if p.is_symlink() and not p.exists()) if path.is_dir() else []
    raw = any((path / name).is_file() or (path / name).is_symlink() for name in ['model.safetensors', 'pytorch_model.bin'])
    problems = []
    if raw and not (path / 'model.bin').is_file():
        problems.append('Transformers weights cannot be loaded by faster-whisper. Select a converted CTranslate2 model.')
    if missing:
        problems.append('Missing/unreadable assets: ' + ', '.join(missing))
    if broken:
        problems.append('Broken cache links: ' + ', '.join(broken))
    if not missing:
        for name in ['config.json', 'tokenizer.json', 'preprocessor_config.json']:
            if not (path / name).exists():
                continue
            try:
                read_json(path / name)
            except AudioToIdeaError as exc:
                problems.append(str(exc))
        if not (path / 'model.bin').stat().st_size:
            problems.append('Model weights are empty')
    return {'path': str(path.resolve()), 'format': 'transformers' if raw else 'ctranslate2',
            'compatible': not problems, 'problems': problems}


def discover(asr):
    root = cache_root(asr)
    found = []
    if root.is_dir():
        for repo in sorted(root.glob('models--*whisper*')):
            for snapshot in sorted((repo / 'snapshots').glob('*')):
                if snapshot.is_dir():
                    item = inspect_model(snapshot)
                    item.update(repository=repo.name.removeprefix('models--').replace('--', '/'), revision=snapshot.name)
                    found.append(item)
    return found


def resolve_model(asr):
    if asr.get('model_path'):
        path = Path(asr['model_path'])
    else:
        repo = cache_root(asr) / ('models--' + asr['model_id'].replace('/', '--'))
        revision = asr.get('revision')
        if not revision:
            ref = repo / 'refs/main'
            revision = ref.read_text().strip() if ref.is_file() else None
        if not revision:
            candidates = [p.name for p in (repo / 'snapshots').glob('*') if inspect_model(p)['compatible']]
            if asr['allow_downloads'] and not asr['offline']:
                from huggingface_hub import snapshot_download
                path = Path(snapshot_download(asr['model_id'], cache_dir=cache_root(asr),
                                             revision=asr.get('revision'),
                                             allow_patterns=['*.bin', '*.json', '*.txt']))
            else:
                raise AudioToIdeaError(f'No selected cached revision for {asr["model_id"]} in {cache_root(asr)}. '
                                       f'Set cache_root/model_path/revision. Compatible revisions: {candidates or "none"}. No download attempted.')
        else:
            # Revisions can be named refs, but never paths escaping this repository.
            if '/' in revision or '\\' in revision or revision in {'.', '..'}:
                raise AudioToIdeaError('Revision must be a snapshot identifier, not a path.')
            path = repo / 'snapshots' / revision
    info = inspect_model(path)
    if not info['compatible']:
        raise AudioToIdeaError(' '.join(info['problems']) + f' Selected directory: {path}. '
                               'Use doctor --discover to list complete compatible snapshots.')
    return info


def execution_device(asr):
    """Ask the actual inference backend, not torch, which hardware it supports."""
    import ctranslate2
    available = ctranslate2.get_cuda_device_count() > 0
    device = asr['device']
    if device == 'auto':
        device = 'cuda' if available else 'cpu'
    if device == 'cuda' and not available:
        raise AudioToIdeaError('CUDA was requested but is unavailable. Choose device=cpu or install compatible CUDA libraries.')
    supported = ctranslate2.get_supported_compute_types(device)
    compute = asr['compute_type']
    if compute == 'auto':
        compute = next((x for x in (['float16', 'int8_float16', 'float32'] if device == 'cuda'
                                   else ['int8', 'int8_float32', 'float32']) if x in supported), None)
    if compute not in supported:
        raise AudioToIdeaError(f'{compute} is unsupported on {device}. Supported compute types: {sorted(supported)}')
    return device, compute


def doctor(settings, include_discovery=False):
    data = settings.data
    report = {'config': str(settings.path), 'settings': data, 'sources': settings.sources,
              'resolved_cache_root': str(cache_root(data['asr'])),
              'dependencies': {x: shutil.which(x) for x in ['ffmpeg', 'ffprobe']}, 'errors': []}
    backend = data['asr'].get('backend', 'faster-whisper')
    if backend == 'faster-whisper':
        try:
            report['model'] = resolve_model({**data['asr'], 'allow_downloads': False})
        except (AudioToIdeaError, OSError) as exc:
            report['errors'].append(str(exc))
        try:
            device, compute = execution_device(data['asr'])
            report['hardware'] = {'device': device, 'compute_type': compute}
        except Exception as exc:
            report['errors'].append(str(exc))
    elif backend == 'transcribe-cpp':
        m_path = data['asr'].get('model_path')
        if m_path and os.path.isfile(m_path):
            report['model'] = {'path': str(m_path), 'compatible': True}
        elif m_path:
            report['errors'].append(f"Model file not found: {m_path}")
        else:
            report['model'] = {'path': 'auto', 'compatible': True}
    elif backend == 'handy-cli':
        h_bin = shutil.which('handy') or '/usr/bin/handy'
        if os.path.isfile(h_bin) and os.access(h_bin, os.X_OK):
            report['model'] = {'path': h_bin, 'compatible': True}
        else:
            report['errors'].append(f"Handy binary not found or not executable: {h_bin}")
    for name, path in report['dependencies'].items():
        if not path:
            report['errors'].append(f'{name} is missing; install FFmpeg.')
    directory = Path(data['output']['directory'] or Path.cwd())
    while not directory.exists() and directory != directory.parent:
        directory = directory.parent
    report['output_parent_writable'] = directory.is_dir() and os.access(directory, os.W_OK)
    if not report['output_parent_writable']:
        report['errors'].append(f'Output parent is not writable: {directory}')
    if include_discovery:
        report['models'] = discover(data['asr'])
    return report
