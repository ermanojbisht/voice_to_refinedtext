"""Human-facing formats derived from the canonical transcript, never vice versa."""
import json
from copy import deepcopy


def timestamp(seconds, separator='.'):
    ms = max(0, round(seconds * 1000))
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    secs, ms = divmod(ms, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}'


def render(transcript, format):
    segments = transcript['segments']
    if format == 'json':
        portable = deepcopy(transcript)
        if isinstance(portable.get('model'), dict):
            portable['model'].pop('path', None)
        return json.dumps(portable, indent=2, ensure_ascii=False) + '\n'
    if format == 'txt':
        return '\n'.join(f'[{timestamp(s["start"])}] {s["text"]}' for s in segments) + '\n'
    if format not in {'srt', 'vtt'}:
        raise ValueError(f'Unsupported format: {format}')
    blocks = []
    for i, s in enumerate(segments, 1):
        sep = ',' if format == 'srt' else '.'
        blocks.append(f'{i}\n{timestamp(s["start"], sep)} --> {timestamp(s["end"], sep)}\n{s["text"]}\n')
    return ('WEBVTT\n\n' if format == 'vtt' else '') + '\n'.join(blocks)
