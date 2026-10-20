"""Bounded paragraph/summary generation; ASR and edited revisions stay intact."""
import json
import re

from .schemas import AudioToIdeaError, check_cancel
from .synthesis import PROMPT_VERSION
from .templates import load_template

TEXT_SCHEMA = {'type': 'object', 'properties': {'text': {'type': 'string'}},
               'required': ['text'], 'additionalProperties': False}


def source_language(text):
    """Make source preservation explicit for Hindi, English and mixed scripts.

    Inspect only recorded text, never segment IDs or template instructions.
    This is a script policy for this app's supported language choices, not a
    replacement for Whisper's acoustic language detection.
    """
    hindi = bool(re.search(r'[\u0900-\u097f]', text))
    english = bool(re.search(r'[A-Za-z]', text))
    if hindi and english:
        return 'Hindi-English mixed; preserve Hindi in Devanagari and English phrases in English without translating either'
    if hindi:
        return 'Hindi; preserve Devanagari Hindi without translating into English'
    return 'English; output English only, without translating into Hindi'


def protected_terms(text, dates=True):
    """Protect observed failure cases: figures, dates and technical acronyms."""
    numbers = re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)*', text)
    days = re.findall(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b|'
                      r'(?:सोमवार|मंगलवार|बुधवार|गुरुवार|शुक्रवार|शनिवार|रविवार)', text, re.I)
    acronyms = re.findall(r'\b[A-Z][a-z]?[A-Z][A-Za-z0-9]*\b', text)
    return sorted(set(numbers + (days if dates else []) + acronyms))


def validate_text(text, source, language):
    for term in protected_terms(source, dates=language == 'source'):
        if term.casefold() not in text.casefold():
            raise AudioToIdeaError('Preserve the original figure/date/technical term: ' + term)
    source_numbers = set(re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)*', source))
    if source_numbers and set(re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)*', text)) - source_numbers:
        raise AudioToIdeaError('Do not change or invent numeric figures from the transcript.')
    if language == 'source':
        source_hindi = bool(re.search(r'[\u0900-\u097f]', source))
        source_english = bool(re.search(r'[A-Za-z]', source))
        result_hindi = bool(re.search(r'[\u0900-\u097f]', text))
        result_english = bool(re.search(r'[A-Za-z]', text))
        if (source_hindi != result_hindi or source_english != result_english):
            raise AudioToIdeaError('Preserve the original Hindi/English scripts and mix; do not translate.')
        if 'नहीं' in source and not re.search(r"नहीं|न\b|\bnot\b|n['’]t\b", text, re.I):
            raise AudioToIdeaError('Preserve the negative statement including नहीं.')
        if re.search(r'\bnot\b', source, re.I) and not re.search(r"\bnot\b|n['’]t\b|नहीं|न\b", text, re.I):
            raise AudioToIdeaError('Preserve the negative statement; payment/approval status must not change.')


def rewrite(transcript, profile, settings, client, cancel=None, notify=None, template=None):
    template = template or load_template(settings)
    language = profile.get('output_language') or settings['synthesis']['output_language']
    effective_language = source_language(' '.join(s['text'] for s in transcript['segments'])) if language == 'source' else language
    guard = ('\nResponse contract: return JSON with exactly one string field named text. '
             'Omit input segment markers such as [S00001]. Required output language: ' + effective_language + '.\n')
    tokens = settings['synthesis']['context_tokens']
    # Byte budgeting covers both Devanagari and Latin scripts conservatively.
    # Reserve response/template/correction space before forming input sections.
    remaining = (tokens - min(4096, tokens // 4) - 512 - 768
                 - len((template.render('', profile['background'], effective_language) + guard).encode())
                 - len(json.dumps(TEXT_SCHEMA).encode()))
    if remaining < 256:
        raise AudioToIdeaError('Prompt/context is too large. Shorten it or increase context_tokens.')
    batches, current, size = [], [], 0
    for segment in transcript['segments']:
        text = segment['text'].strip()
        while text:
            count = min(len(text), max(1, (remaining - 32) // 4))
            # Prefer word boundaries. Unbroken strings still split safely.
            if count < len(text) and ' ' in text[:count]:
                count = text.rfind(' ', 0, count) + 1
            piece, text = text[:count], text[count:]
            line = f'[{segment["id"]}] {piece}\n'
            length = len(line.encode())
            if current and size + length > remaining:
                batches.append(current)
                current, size = [], 0
            current.append(line)
            size += length
    if current:
        batches.append(current)
    parts = []
    for index, lines in enumerate(batches):
        check_cancel(cancel)
        if notify:
            notify({'stage': 'synthesis', 'current': index + 1, 'total': len(batches),
                    'message': f'Creating {template.mode.replace("_", " ")} section {index + 1}/{len(batches)}'})
        recorded = ''.join(lines)
        source = re.sub(r'^\[S\d+\] ', '', recorded, flags=re.M)
        protected = protected_terms(source, dates=language == 'source')
        hint = ''
        for term in protected:
            candidate = hint + (', ' if hint else '') + term
            if len(candidate.encode()) > 400:
                break
            hint = candidate
        prompt = guard + ('\nKeep these tokens exactly: ' + hint + '\n' if hint else '')
        prompt += template.render(recorded, profile['background'], effective_language)
        for attempt in range(2):
            result = client.generate(prompt, TEXT_SCHEMA)
            error = 'Return a nonempty paragraph in the JSON text field, without extra fields.'
            if (isinstance(result, dict) and set(result) == {'text'}
                    and isinstance(result['text'], str) and result['text'].strip()):
                try:
                    validate_text(result['text'], source, language)
                    parts.append(result['text'].strip())
                    break
                except AudioToIdeaError as exc:
                    error = str(exc)
            if attempt:
                raise AudioToIdeaError('Processing failed validation: ' + error + ' Transcript is preserved; retry processing.')
            check_cancel(cancel)
            prompt += '\nValidation correction: ' + error + '\nReturn the corrected JSON text field.\n'
    return {'mode': template.mode, 'text': '\n\n'.join(parts), 'parts': parts,
            'transcript_revision': transcript['revision'], 'model': settings['synthesis']['model'],
            'output_language': language, 'prompt_version': PROMPT_VERSION, 'prompt_sha256': template.digest}
