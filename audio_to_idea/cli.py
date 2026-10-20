"""Command-line interface with no display, keyboard, microphone or GUI imports."""
import argparse
import json
from pathlib import Path
import signal
import sys
import threading

from . import __version__
from .config import load_settings
from .jobs import JobService, destination, inputs
from .llm import OllamaClient
from .models import doctor
from .schemas import AudioToIdeaError, Cancelled
from .watcher import Watcher
from .templates import MODES


def parser():
    root = argparse.ArgumentParser(prog='audio2idea', description='Local audio files → timestamped transcripts and evidence-linked ideas.')
    root.add_argument('--version', action='version', version=__version__)
    root.add_argument('--config', help='Versioned module settings JSON; relative paths resolve from this file.')
    sub = root.add_subparsers(dest='command', required=True)
    for name in ['transcribe', 'process', 'watch', 'doctor', 'gui']:
        p = sub.add_parser(name)
        p.add_argument('--config', default=argparse.SUPPRESS)
        p.add_argument('--model', help='Local CTranslate2 model/snapshot directory (not raw Transformers weights).')
        p.add_argument('--model-id', help='Cached repository ID or supported model alias.')
        p.add_argument('--cache-root', help='Hugging Face hub cache folder on this PC.')
        p.add_argument('--revision', help='Explicit snapshot identifier; never chooses an arbitrary revision.')
        p.add_argument('--device', choices=['auto', 'cpu', 'cuda'])
        p.add_argument('--compute-type')
        p.add_argument('--json', action='store_true', help='Machine-readable results; progress goes to stderr.')
        if name in {'process', 'watch', 'gui'}:
            p.add_argument('--mode', choices=list(MODES), help='Processing task; default: clean_paragraph.')
            p.add_argument('--prompt-file', help='Custom UTF-8 prompt for the selected mode; requires {transcript}.')
            p.add_argument('--output-language', choices=['source', 'English', 'Hindi'], help='source preserves Hindi/English/mixed speech; other choices translate.')
        if name == 'doctor':
            p.add_argument('--discover', action='store_true', help='List cached models and compatibility problems.')
            p.add_argument('--check-ollama', action='store_true', help='Check the configured local service without inference.')
        if name in {'transcribe', 'process', 'watch'}:
            p.add_argument('--input', '-i', required=True, help='Recording file or folder (watch requires a folder).')
            p.add_argument('--output-dir', '-o', help='Output folder; by default beside each input file.')
            p.add_argument('--format', '-f', choices=['txt', 'srt', 'vtt', 'json'], action='append', help='Repeat for multiple transcript formats.')
            p.add_argument('--language', help='auto preserves mixed Hindi/English; otherwise use a language code.')
            p.add_argument('--chunk-size', type=float, help='Chunk duration in seconds, including overlapping boundaries.')
            p.add_argument('--overlap', type=float, help='Chunk overlap in seconds; smaller than chunk size.')
            p.add_argument('--overwrite', action='store_true', default=None, help='Re-run ASR/ideas. Unrelated/manually edited outputs remain protected.')
            p.add_argument('--context', '-c', default='', help='Background for interpretation; not spoken evidence.')
            p.add_argument('--context-file', help='UTF-8 background context; combined with inline context and selected profile.')
            p.add_argument('--profile', help='JSON context profile with glossary, or a plain text/Markdown file.')
            p.add_argument('--synthesis-model', help='Ollama idea model; separate from --model (ASR).')
            p.add_argument('--ollama-host')
            p.add_argument('--no-summary', action='store_true', help='Keep transcript only; no Ollama request.')
        if name == 'watch':
            p.add_argument('--stable-seconds', type=float)
            p.add_argument('--poll-seconds', type=float)
            p.add_argument('--recursive', action='store_true', default=None)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    mapping = {'model': 'asr.model_path', 'model_id': 'asr.model_id', 'cache_root': 'asr.cache_root',
               'revision': 'asr.revision', 'device': 'asr.device', 'compute_type': 'asr.compute_type',
               'language': 'asr.language', 'chunk_size': 'audio.chunk_seconds', 'overlap': 'audio.overlap_seconds',
               'format': 'output.formats', 'overwrite': 'output.overwrite', 'output_dir': 'output.directory',
               'synthesis_model': 'synthesis.model', 'ollama_host': 'synthesis.host', 'profile': 'synthesis.context_profile',
               'stable_seconds': 'watch.stable_seconds', 'poll_seconds': 'watch.poll_seconds', 'recursive': 'watch.recursive',
               'mode': 'synthesis.mode', 'prompt_file': 'synthesis.prompt_file', 'output_language': 'synthesis.output_language'}
    cancel = threading.Event()
    previous = None
    try:
        settings = load_settings(args.config, {key: getattr(args, name, None) for name, key in mapping.items()})
        if args.command == 'gui':
            try:
                from audio_to_idea_launcher import launch_audio_idea_app
                launch_audio_idea_app()
                return 0
            except Exception:
                try:
                    from .gui import launch
                    launch(settings)
                    return 0
                except ImportError as exc:
                    raise AudioToIdeaError('Desktop components are unavailable.') from exc
        if args.command == 'doctor':
            report = doctor(settings, args.discover)
            if args.check_ollama:
                client = OllamaClient(settings.data)
                try:
                    report['ollama'] = client.readiness()
                    if not report['ollama']['ready']:
                        report['errors'].append('Selected synthesis model is not available in Ollama.')
                except AudioToIdeaError as exc:
                    report['errors'].append(str(exc))
                finally:
                    client.close()
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2 if report['errors'] else 0
        if threading.current_thread() is threading.main_thread():
            previous = signal.signal(signal.SIGINT, lambda *_: cancel.set())
        context = args.context
        if args.context_file:
            context = '\n\n'.join([Path(args.context_file).expanduser().read_text(encoding='utf-8'), context])
        summary = args.command != 'transcribe' and not args.no_summary
        service = JobService(settings)

        def notify(event):
            if args.json:
                print(json.dumps(event, ensure_ascii=False), file=sys.stderr, flush=True)
            else:
                print(f'{event["stage"]}: {event["message"]}', file=sys.stderr, flush=True)

        if args.command == 'watch':
            Watcher(service, args.input, settings.data['output']['directory'], summary, context,
                    settings.data['synthesis']['context_profile'], notify).run(cancel)
            return 130 if cancel.is_set() else 0
        files = inputs(args.input)
        if not files:
            raise AudioToIdeaError('No supported recordings found in this folder.')
        results = []
        for source in files:
            if cancel.is_set():
                break
            output, name = destination(source, Path(args.input).expanduser().resolve(), settings.data['output']['directory'])
            results.append(service.run(source, output, name, summary, context,
                                        settings.data['synthesis']['context_profile'], cancel, notify))
        if args.json:
            print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
        else:
            for result in results:
                print(f'{Path(result["source"]).name}: {result["status"]}')
                for path in result['outputs']:
                    print('  ' + path)
                if result.get('error'):
                    print('  ' + result['error'])
        if cancel.is_set() or any(r['status'] == 'cancelled' for r in results):
            return 130
        return 3 if any(r['status'] != 'complete' for r in results) else 0
    except (AudioToIdeaError, OSError, ValueError) as exc:
        print(f'audio2idea: {exc}', file=sys.stderr)
        return 2
    finally:
        if previous is not None:
            signal.signal(signal.SIGINT, previous)


def gui_main():
    """Installed GUI entry point retains the optional-dependency explanation."""
    return main(['gui'])

