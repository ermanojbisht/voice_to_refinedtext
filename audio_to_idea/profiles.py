"""Context profiles are background, not proof of what was spoken."""
from pathlib import Path

from .schemas import AudioToIdeaError
from .storage import read_json


def load_profile(path=None, context=''):
    profile = {'title': 'Recording context', 'background': '', 'glossary': [], 'output_language': None}
    if path:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise AudioToIdeaError(f'Context profile does not exist: {path}')
        if path.suffix.lower() == '.json':
            raw = read_json(path)
            if not isinstance(raw, dict):
                raise AudioToIdeaError('Context profile must be a JSON object.')
            profile.update(raw)
        else:
            try:
                profile.update(title=path.stem, background=path.read_text(encoding='utf-8'))
            except OSError as exc:
                raise AudioToIdeaError(f'Cannot read context profile: {exc}') from exc
    if not isinstance(profile['background'], str) or not isinstance(profile['title'], str):
        raise AudioToIdeaError('Profile title and background must be strings.')
    if not isinstance(profile['glossary'], list) or any(not isinstance(x, str) for x in profile['glossary']):
        raise AudioToIdeaError('Profile glossary must be a list of terms.')
    profile['background'] = '\n\n'.join(x for x in [profile['background'], context.strip()] if x)
    return profile

