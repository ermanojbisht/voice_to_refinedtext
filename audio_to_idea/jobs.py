"""One durable processing service used by CLI, GUI and watcher.

Stage fingerprints separate ASR, edited transcript, synthesis and export. A
failed idea request must never discard a valid transcript or re-run its ASR.
"""
from copy import deepcopy
import datetime
import hashlib
import json
from pathlib import Path
import tempfile
import time

from .audio import EXTENSIONS, chunks, pause_guided_chunks, prepare
from .exports import render
from .llm import OllamaClient
from .merging import merge_chunks
from .models import resolve_model
from .profiles import load_profile
from .rewriting import rewrite
from .schemas import AudioToIdeaError, Cancelled, check_cancel
from .storage import atomic_write, file_hash, file_lock, fingerprint, read_json, write_json
from .synthesis import PROMPT_VERSION, extract, render_ideas
from .transcription import Transcriber
from .templates import load_template


def inputs(path, recursive=True):
    path = Path(path).expanduser().resolve()
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise AudioToIdeaError(f'Input does not exist: {path}')
    return sorted(p for p in (path.rglob('*') if recursive else path.glob('*'))
                  if p.is_file() and p.suffix.lower() in EXTENSIONS
                  and not any(part == '.audio2idea' or part.startswith('.audio2idea-') for part in p.parts))


def destination(source, input_root, output_root=None):
    """Preserve folders and disambiguate same stems without flattening a batch."""
    source, root = Path(source), Path(input_root)
    relative = source.parent.relative_to(root) if root.is_dir() else Path()
    directory = Path(output_root) / relative if output_root else source.parent
    siblings = [p for p in source.parent.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS
                and p.stem.casefold() == source.stem.casefold()]
    name = source.stem if len(siblings) == 1 else source.stem + '__' + source.suffix[1:].lower()
    if len({p.suffix.casefold() for p in siblings}) < len(siblings):
        name += '-' + fingerprint(source.name)[:6]
    return directory, name


class JobService:
    def __init__(self, settings, transcriber_factory=Transcriber, client_factory=OllamaClient):
        self.settings = deepcopy(settings.data if hasattr(settings, 'data') else settings)
        self.transcriber_factory, self.client_factory = transcriber_factory, client_factory
        self._template = None

    def snapshot_prompt(self):
        """Freeze template bytes for a batch; a new service sees later edits."""
        if self._template is None:
            self._template = load_template(self.settings)
        return self._template

    def run(self, source, output=None, name=None, summary=True, context='', profile=None, cancel=None, notify=None):
        """Process/resume one source; return a status instead of aborting a batch."""
        started = time.monotonic()
        cfg = self.settings
        source = Path(source).expanduser().resolve()
        directory = Path(output or cfg['output']['directory'] or source.parent).resolve()
        if name is None:
            _, name = destination(source, source)
        key = fingerprint(str(source))[:20]
        workspace = directory / '.audio2idea' / key
        result = {'source': str(source), 'workspace': str(workspace), 'status': 'failed', 'outputs': []}
        notify = notify or (lambda event: None)
        backend = None
        client = None
        manifest = None
        valid_manifest = False
        manifest_path = workspace / 'manifest.json'
        lock = file_lock(workspace / 'job.lock', cancel)
        acquired = False
        try:
            lock.__enter__()
            acquired = True
            manifest = read_json(manifest_path, {'version': 1, 'source': str(source), 'artifacts': {}, 'chunks': {}})
            if manifest.get('version') != 1 or manifest.get('source') != str(source):
                raise AudioToIdeaError('Job manifest version/source mismatch; choose another output folder.')
            valid_manifest = True
            manifest['status'] = 'running'

            # 3-Portion Acoustic Language Identification & Non-Blocking Suggestion Check
            notify({'stage': 'acoustic_analysis', 'message': 'Checking audio language acoustics (Start, Middle, End)...'})
            try:
                from .asr.acoustic_langid import AcousticLanguageDetector, get_acoustic_suggestion
                det = AcousticLanguageDetector.get_instance().detect(str(source))
                manifest['acoustic_info'] = det
                result['acoustic_info'] = det
                active_profile = cfg.get('asr', {}).get('active_profile') or cfg.get('active_preset') or 'smart_bilingual'
                sug = get_acoustic_suggestion(det, active_profile)
                if sug:
                    manifest['acoustic_suggestion'] = sug
                    result['acoustic_suggestion'] = sug
                    notify({'stage': 'acoustic_suggestion', 'suggestion': sug, 'message': sug.get('message')})
            except Exception:
                pass

            write_json(manifest_path, manifest)
            check_cancel(cancel)
            template = self.snapshot_prompt() if summary else None
            profile_data = load_profile(profile or cfg['synthesis']['context_profile'], context)
            source_identity = file_hash(source)

            backend_type = str(cfg['asr'].get('backend', 'faster-whisper')).lower().replace('-', '_')
            if backend_type in ('transcribe_cpp', 'handy_cli'):
                model_target = Path(cfg['asr'].get('model_path') or cfg['asr'].get('model_id') or '')
                if model_target.is_file():
                    model_identity = {
                        'path': str(model_target),
                        'size': model_target.stat().st_size,
                        'mtime_ns': model_target.stat().st_mtime_ns,
                        'config_hash': file_hash(model_target),
                    }
                    model_info = {'path': str(model_target), 'problems': [], 'compatible': True}
                else:
                    model_identity = {'backend': backend_type, 'path': str(model_target)}
                    model_info = {'path': str(model_target), 'problems': [], 'compatible': True}
            else:
                model_info = resolve_model(cfg['asr'])
                weights = Path(model_info['path']) / 'model.bin'
                model_identity = {'path': model_info['path'], 'size': weights.stat().st_size,
                                  'mtime_ns': weights.stat().st_mtime_ns,
                                  'config_hash': file_hash(Path(model_info['path']) / 'config.json')}
            # Bump pipeline_version if chunk/merge interpretation changes so old
            # transcripts cannot silently represent a different ASR algorithm.
            asr_key = fingerprint({'pipeline_version': 1, 'source': source_identity, 'model': model_identity, 'asr': cfg['asr'],
                                   'audio': cfg['audio'], 'glossary': profile_data['glossary']})
            transcript_path = workspace / f'transcript-{asr_key}.json'
            reuse = transcript_path.is_file() and not cfg['output']['overwrite']
            if reuse:
                transcript = read_json(transcript_path)
                notify({'stage': 'transcription', 'message': 'Reusing verified transcript; no ASR needed'})
            else:
                notify({'stage': 'preparation', 'message': 'Preparing audio; original recording is preserved'})
                with tempfile.TemporaryDirectory(prefix='.audio2idea-') as temp:
                    prepared, duration = prepare(source, temp, cfg['audio'], cancel)
                    if cfg['audio'].get('pause_guided', False):
                        windows = list(pause_guided_chunks(
                            prepared,
                            target_seconds=cfg['audio'].get('chunk_seconds'),
                            min_chunk_seconds=cfg['audio'].get('min_chunk_seconds'),
                            max_chunk_seconds=cfg['audio'].get('max_chunk_seconds'),
                            min_pause_ms=cfg['audio'].get('min_pause_ms'),
                        ))
                    else:
                        windows = list(chunks(duration, cfg['audio']['chunk_seconds'], cfg['audio']['overlap_seconds']))
                    raw = []
                    backend = self.transcriber_factory(cfg, model_info, cancel, notify)
                    for window in windows:
                        check_cancel(cancel)
                        checkpoint = workspace / 'chunks' / asr_key / f'{window.index:06d}.json'
                        notify({'stage': 'transcription', 'current': window.index + 1, 'total': len(windows),
                                'message': f'Transcribing chunk {window.index + 1}/{len(windows)}'})
                        item = read_json(checkpoint) if checkpoint.exists() and not cfg['output']['overwrite'] else None
                        if item is None:
                            item = backend.transcribe(prepared, window, ', '.join(profile_data['glossary']))
                            write_json(checkpoint, item)
                        if item['index'] != window.index or abs(item['start'] - window.start) > .001 or abs(item['end'] - window.end) > .001:
                            raise AudioToIdeaError('Chunk checkpoint has inconsistent coverage; choose overwrite to regenerate it.')
                        raw.append(item)
                if file_hash(source) != source_identity:
                    raise AudioToIdeaError('Source changed during processing; retry after copying finishes.')
                segments, warnings = merge_chunks(raw, duration)
                if not segments:
                    warnings.append('No speech was recognized. Review the source recording before treating this as an empty transcript.')
                transcript = {'version': 1, 'revision': asr_key, 'source_name': source.name,
                              'processed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                              'source_sha256': source_identity, 'duration': duration, 'segments': segments,
                              'chunks': raw, 'model': {**model_info, 'repository': cfg['asr']['model_id'],
                                                       'revision': Path(model_info['path']).name}, 'warnings': warnings}
                write_json(transcript_path, transcript)
            if backend and cfg['jobs']['release_asr_before_synthesis']:
                backend.close()
                backend = None
            edit = manifest.get('edit')
            if edit and edit['raw_revision'] == asr_key:
                transcript = read_json(workspace / edit['filename'])
            manifest['transcript'] = transcript_path.name
            manifest['revision'] = transcript['revision']
            manifest['source_sha256'] = source_identity
            result['transcript_path'] = str(workspace / edit['filename']) if edit and edit['raw_revision'] == asr_key else str(transcript_path)

            def publish(target, text):
                target = Path(target)
                digest = hashlib.sha256(text.encode()).hexdigest()
                old = manifest['artifacts'].get(target.name)
                allow_overwrite = cfg['output'].get('overwrite', False) or cfg['output'].get('allow_overwrite', False)
                if target.exists() and not allow_overwrite:
                    if file_hash(target) != digest and (not old or file_hash(target) not in {old.get('sha256'), old.get('pending')}):
                        raise AudioToIdeaError(f'Output contains unrelated or manually edited content: {target}. '
                                               'Use a different output folder or save edits through the transcript editor.')
                # Reserve ownership before writing, so a crash after the rename
                # can be recognized without assuming any same-stem file is ours.
                manifest['artifacts'][target.name] = {**(old or {}), 'pending': digest}
                write_json(manifest_path, manifest)
                atomic_write(target, text)
                manifest['artifacts'][target.name] = {'sha256': digest}
                write_json(manifest_path, manifest)
                result['outputs'].append(str(target))

            for format in cfg['output']['formats']:
                publish(directory / f'{name}.{format}', render(transcript, format))
            manifest['status'] = 'transcribed'
            write_json(manifest_path, manifest)
            if summary:
                check_cancel(cancel)
                idea_key = fingerprint({'transcript': transcript['revision'], 'profile': profile_data,
                                        'settings': cfg['synthesis'], 'prompt': PROMPT_VERSION,
                                        'template_sha256': template.digest})
                mode = template.mode
                idea_path = workspace / f'{"ideas" if mode == "ideas_actions" else "processed"}-{idea_key}.json'
                if idea_path.exists() and not cfg['output']['overwrite']:
                    ideas = read_json(idea_path)
                    notify({'stage': 'synthesis', 'message': 'Reusing processed output for this transcript and prompt'})
                else:
                    client = self.client_factory(cfg, cancel, notify)
                    if mode == 'ideas_actions':
                        ideas = extract(transcript, profile_data, cfg, client, cancel, notify, template)
                        ideas.update(mode=mode, prompt_sha256=template.digest)
                    else:
                        ideas = rewrite(transcript, profile_data, cfg, client, cancel, notify, template)
                    write_json(idea_path, ideas)
                suffix_map = {
                    'clean_paragraph': 'clean',
                    'clean_bilingual': 'bilingual',
                    'official_english': 'english',
                    'official_hindi': 'hindi',
                    'roman_hinglish': 'hinglish',
                    'concise_summary': 'summary',
                    'ideas_actions': 'idea'
                }
                suffix = suffix_map.get(mode, 'processed')
                processed_path = directory / f'{name}_{suffix}.txt'
                text = render_ideas(ideas, transcript) if mode == 'ideas_actions' else ideas['text'] + '\n'
                publish(processed_path, text)
                result.update(synthesis_mode=mode, processed_path=str(processed_path), synthesis_path=str(idea_path))
                manifest.setdefault('processed', {})[mode] = idea_path.name
                if mode == 'ideas_actions':
                    manifest['ideas'] = idea_path.name  # Keep earlier structured-job readers compatible.
            metadata = {'version': 1, 'source_name': source.name, 'source_sha256': source_identity,
                        'duration': transcript['duration'], 'revision': transcript['revision'],
                        'asr_model_id': cfg['asr']['model_id'], 'snapshot': Path(model_info['path']).name,
                        'languages': sorted({c['language'] for c in transcript['chunks'] if c.get('language')}),
                        'context_title': profile_data['title'], 'summary_generated': summary,
                        'synthesis_mode': template.mode if template else None,
                        'synthesis_model': cfg['synthesis']['model'] if template else None,
                        'prompt_sha256': template.digest if template else None,
                        'processing_seconds': round(time.monotonic() - started, 3),
                        'warnings': transcript['warnings']}
            if cfg['output']['save_metadata']:
                publish(directory / f'{name}.meta.json', json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
            manifest['status'] = result['status'] = 'complete'
            manifest.pop('error', None)
            write_json(manifest_path, manifest)
        except Cancelled as exc:
            result.update(status='cancelled', error=str(exc))
        except Exception as exc:
            result.update(status='partial' if result.get('transcript_path') else 'failed', error=str(exc))
        finally:
            try:
                if backend:
                    backend.close()
                if client and hasattr(client, 'close'):
                    client.close()
                if acquired and valid_manifest and result['status'] != 'complete':
                    # Keep ownership through failure persistence; releasing and
                    # reacquiring could overwrite another process's newer state.
                    manifest.update(status=result['status'], error=result.get('error', ''))
                    try:
                        write_json(manifest_path, manifest)
                    except OSError as exc:
                        result['error'] = result.get('error', '') + f' State could not be persisted: {exc}'
            finally:
                if acquired:
                    lock.__exit__(None, None, None)
        notify({'stage': result['status'], 'message': result.get('error', 'Completed'), 'result': result})
        return result


def save_transcript_edit(workspace, text_by_id):
    """Save a new revision without changing raw ASR, timing, or unrelated files."""
    workspace = Path(workspace)
    with file_lock(workspace / 'job.lock', wait=False):
        manifest = read_json(workspace / 'manifest.json')
        raw = read_json(workspace / manifest['transcript'])
        if set(text_by_id) != {s['id'] for s in raw['segments']}:
            raise AudioToIdeaError('Keep every segment ID when editing a transcript.')
        edited = deepcopy(raw)
        for segment in edited['segments']:
            if not isinstance(text_by_id[segment['id']], str):
                raise AudioToIdeaError('Transcript edits must be text.')
            segment['text'] = text_by_id[segment['id']]
            segment['words'] = []  # Original word timings do not describe corrected text.
        edited['raw_revision'] = raw['revision']
        edited['revision'] = fingerprint({'raw': raw['revision'], 'edits': text_by_id})
        filename = f'edited-{edited["revision"]}.json'
        write_json(workspace / filename, edited)
        manifest['edit'] = {'raw_revision': raw['revision'], 'filename': filename}
        manifest['status'] = 'transcribed'
        write_json(workspace / 'manifest.json', manifest)
        return workspace / filename
