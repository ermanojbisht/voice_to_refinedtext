"""Editable, portable prompt templates with a fixed model response contract.

Only known placeholders are substituted, once. Transcript text containing
braces is never interpreted as another template or Python format expression.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

from .schemas import AudioToIdeaError

MODES = {'clean_paragraph': '1. Clean paragraph',
         'concise_summary': '2. Concise summary',
         'ideas_actions': '3. Ideas and actions'}
BUILTINS = Path(__file__).parent / 'prompt_templates'
FIELDS = {'transcript', 'context', 'output_language'}
PLACEHOLDER = re.compile(r'\{([a-zA-Z_]\w*)\}')


def validate_template(text):
    if not isinstance(text, str) or not text.strip() or len(text.encode('utf-8')) > 65536:
        raise AudioToIdeaError('Prompt must be nonempty UTF-8 text of at most 64 KiB.')
    unknown = set(PLACEHOLDER.findall(text)) - FIELDS
    if unknown:
        raise AudioToIdeaError('Unknown prompt placeholders: ' + ', '.join(sorted(unknown)))
    if text.count('{transcript}') != 1:
        raise AudioToIdeaError('Prompt must contain {transcript} exactly once.')
    return text


@dataclass(frozen=True)
class Template:
    text: str
    path: Path
    mode: str

    @property
    def digest(self):
        return hashlib.sha256(self.text.encode('utf-8')).hexdigest()

    def render(self, transcript, context='', output_language='source'):
        values = {'transcript': transcript, 'context': context, 'output_language': output_language}
        return PLACEHOLDER.sub(lambda match: values[match[1]], self.text)


def load_template(settings, mode=None):
    cfg = settings['synthesis']
    mode = mode or cfg.get('mode', 'clean_paragraph')
    if mode not in MODES:
        raise AudioToIdeaError('Unknown processing mode: ' + str(mode))
    path = BUILTINS / f'{mode}.txt'
    if cfg.get('prompt_file'):
        path = Path(cfg['prompt_file']).expanduser()
    elif cfg.get('prompt_directory'):
        candidate = Path(cfg['prompt_directory']).expanduser() / f'{mode}.txt'
        # A missing mode file uses its packaged default, but a broken symlink
        # or unreadable chosen file must report a problem instead of falling back.
        if candidate.exists() or candidate.is_symlink():
            path = candidate
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as exc:
        raise AudioToIdeaError(f'Cannot read prompt template {path}: {exc}') from exc
    return Template(validate_template(text), path.resolve(), mode)
