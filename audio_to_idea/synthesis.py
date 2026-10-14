"""Section extraction with explicit evidence and conservative context budgets."""
import json
import re
import unicodedata
from copy import deepcopy

from .exports import timestamp
from .schemas import AudioToIdeaError, check_cancel
from .templates import load_template

SECTIONS = {
    'bottlenecks': 'Core Operational Bottlenecks / Observations',
    'proposals': 'Actionable Proposals / Solutions',
    'implications': 'Institutional / Regulatory Implications',
}
ITEM = {'type': 'object', 'properties': {'text': {'type': 'string', 'minLength': 1},
         'evidence': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1},
         'kind': {'type': 'string', 'enum': ['spoken', 'inferred']}},
         'required': ['text', 'evidence', 'kind'], 'additionalProperties': False}
SCHEMA = {'type': 'object', 'properties': {key: {'type': 'array', 'items': ITEM} for key in SECTIONS},
          'required': list(SECTIONS), 'additionalProperties': False}
PROMPT_VERSION = 5


def _normalized(text):
    """Compare quotes without whitespace/case/Unicode representation noise."""
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text).casefold()).strip()


def _check_duplicates(sections):
    # IDs locate evidence but do not validate category membership. Never present
    # a copied sentence in several categories as several independent findings.
    categories = {}
    for key, items in sections.items():
        for item in items:
            normalized = _normalized(item['text']).strip(' .,:;!?।…')
            if normalized in categories and categories[normalized] != key:
                raise AudioToIdeaError('Synthesis repeated the same finding across categories. '
                                       'Transcript is preserved; retry ideas or choose another idea model.')
            categories[normalized] = key


def _speech_only_item(text):
    """Exclude literal copy/repeat tests, without dropping adjacent work facts.

    Small models can persistently classify these as proposals despite the
    prompt. Only discard an item when every sentence is a speech-only request
    or a greeting/reassurance; any substantive sentence keeps normal review.
    """
    sentences = [s.strip() for s in re.split(r'[.!?।]+', _normalized(text)) if s.strip()]
    request = r'(?:please )?(?:copy|repeat|transcribe|write down) (?:my|these|the) (?:words|speech|recording|transcript)(?: and (?:tell|read|repeat)(?: them)?(?: back)?(?: to)? me)?'
    casual = r'(?:hello|hi|thank you|i (?:think|hope) you are (?:fine|well|okay))'
    return bool(sentences) and all(re.fullmatch(request + '|' + casual, s) for s in sentences)


def _validate_findings(result, allowed, transcript, language='source'):
    if not isinstance(result, dict) or set(result) != set(SECTIONS):
        raise AudioToIdeaError('Synthesis did not return the three required sections.')
    cleaned = {key: [] for key in SECTIONS}
    for key in SECTIONS:
        if not isinstance(result[key], list):
            raise AudioToIdeaError(f'Invalid synthesis section: {key}')
        for item in result[key]:
            if (not isinstance(item, dict) or not isinstance(item.get('text'), str) or not item['text'].strip()
                or item.get('kind') not in {'spoken', 'inferred'} or not isinstance(item.get('evidence'), list)
                or not item['evidence'] or any(not isinstance(s, str) or s not in allowed for s in item['evidence'])):
                raise AudioToIdeaError('Synthesis contains invalid or unsupported evidence references; review/retry is required.')
            item = {**item, 'evidence': sorted(set(item['evidence']))}
            if item['kind'] == 'spoken':
                source_text = ' '.join(s['text'] for s in transcript['segments'] if s['id'] in item['evidence'])
                # Translation remains supported. In another output language the
                # model must also supply an original-language source quotation;
                # checking translated words against Hindi verbatim would fail.
                quote = item['text'] if language == 'source' else item.get('quote', '')
                if not isinstance(quote, str) or not quote.strip() or _normalized(quote) not in _normalized(source_text):
                    raise AudioToIdeaError('Synthesis marked text as spoken that is not in its cited transcript. '
                                           'Transcript is preserved; review/retry ideas.')
            if not _speech_only_item(item['text']):
                cleaned[key].append(item)
    _check_duplicates(cleaned)
    return cleaned


def extract(transcript, profile, settings, client, cancel=None, notify=None, template=None):
    language = profile.get('output_language') or settings['synthesis']['output_language']
    schema_template = deepcopy(SCHEMA)
    spoken_rule = ('For kind=spoken, text must be a short verbatim excerpt from its cited transcript segments, '
                   'not a paraphrase or a quotation from these instructions/background. ')
    if language != 'source':
        spoken_rule = ('Write text in the requested output language. Include quote: a short verbatim excerpt '
                       'in the original recording language from the cited transcript segments. '
                       'Never quote these instructions/background as recording evidence. ')
        for section in schema_template['properties'].values():
            section['items']['properties']['quote'] = {'type': 'string', 'minLength': 1}
            section['items']['required'].append('quote')
    # Direct callers keep the structured extraction API; the job service chooses
    # between this mode and paragraph/summary processing explicitly.
    template = template or load_template(settings, mode='ideas_actions')
    guard = ('\nResponse contract: return JSON with bottlenecks, proposals and implications; '
             'each item needs text, evidence segment IDs and kind=spoken or inferred. '
             + spoken_rule + '\nA recording consisting only of reassurance or requests to copy/repeat speech '
             'has no operational findings: all three arrays must be empty, regardless of project background.\n')
    introduction = guard + template.render('', profile['background'], language)
    # UTF-8 byte count is a conservative upper bound for byte-based tokenizers.
    # Reserve output/template room rather than relying on a characters/4 guess.
    tokens = settings['synthesis']['context_tokens']
    budget = tokens - min(4096, tokens // 4) - 512
    remaining = budget - len(introduction.encode('utf-8')) - len(json.dumps(schema_template).encode())
    if remaining < 256:
        raise AudioToIdeaError('Context profile is too large for this context budget. Shorten background or increase context_tokens.')
    batches, current, length = [], [], 0
    for segment in transcript['segments']:
        # Split pathological long segments while keeping their original evidence ID.
        pieces, text = [], segment['text']
        while text:
            count = min(len(text), max(1, remaining // 4))
            part, text = text[:count], text[count:]
            pieces.append(f'[{segment["id"]}] {part}\n')
        for line in pieces:
            size = len(line.encode('utf-8'))
            if current and length + size > remaining:
                batches.append(current)
                current, length = [], 0
            if size > remaining:
                raise AudioToIdeaError('A transcript segment exceeds the available context budget.')
            current.append(line)
            length += size
    if current:
        batches.append(current)
    combined = {key: [] for key in SECTIONS}
    for index, lines in enumerate(batches):
        check_cancel(cancel)
        if notify:
            notify({'stage': 'synthesis', 'current': index + 1, 'total': len(batches),
                    'message': f'Extracting ideas from section {index + 1}/{len(batches)}'})
        allowed = {line.split(']')[0][1:] for line in lines}
        schema = deepcopy(schema_template)
        for section in schema['properties'].values():
            # Constrain the decoder to IDs that actually appear in this section.
            # Small models otherwise invent IDs even with clear instructions.
            section['items']['properties']['evidence']['items']['enum'] = sorted(allowed)
        prompt = guard + template.render(''.join(lines), profile['background'], language)
        for attempt in range(2):
            result = client.generate(prompt, schema)
            try:
                result = _validate_findings(result, allowed, transcript, language)
                break
            except AudioToIdeaError as exc:
                if attempt:
                    raise
                check_cancel(cancel)
                # One bounded correction can repair a small model's category or
                # quotation mistake without repeating ASR or accepting bad data.
                # Its instruction fits the template reserve in the prompt budget.
                correction = str(exc)[:300]
                prompt = (guard + template.render(''.join(lines), profile['background'], language) +
                          '\nValidation correction: ' + correction +
                          '\nReturn the complete corrected JSON. Use empty arrays where unsupported. '
                          'An ordinary project delay/action is not an institutional implication.\n')
                if notify:
                    notify({'stage': 'synthesis', 'message': 'Correcting unsupported or repeated findings (one retry)'})
        for key in SECTIONS:
            for item in result[key]:
                # Consolidate exact repeated findings deterministically. Avoid a
                # second free-form summary that could lose their source references.
                old = next((x for x in combined[key] if x['text'].strip().casefold() == item['text'].strip().casefold()
                            and x['kind'] == item['kind']), None)
                if old:
                    old['evidence'] = sorted(set(old['evidence'] + item['evidence']))
                else:
                    combined[key].append(item)
    _check_duplicates(combined)
    return {'sections': combined, 'transcript_revision': transcript['revision'],
            'context_title': profile['title'], 'model': settings['synthesis']['model'], 'prompt_version': PROMPT_VERSION}


def render_ideas(ideas, transcript):
    ids = {s['id']: s for s in transcript['segments']}
    # An empty analysis is an ordinary successful result, not a reason to pad a
    # short recording with three executive-report headings. Full processing
    # identity remains in the structured ideas, manifest and metadata sidecar.
    if not any(ideas['sections'].values()):
        return ('# Ideas & actions\n'
                f'**Source Audio:** {transcript["source_name"]} | **Duration:** {timestamp(transcript["duration"])}\n\n'
                'No actionable ideas identified in this recording.\n')
    lines = ['# EXECUTIVE BRIEF & ACTIONABLE SYNTHESIS',
             f'**Source Audio:** {transcript["source_name"]} | **Duration:** {timestamp(transcript["duration"])}',
             f'**Context Applied:** {ideas["context_title"]}',
             f'**Processed:** {transcript.get("processed_at", "not recorded")}',
             f'**Transcript revision:** {ideas["transcript_revision"]} | **Model:** {ideas["model"]}',
             '', 'ASR and AI output require review. Inferred items are labeled explicitly.', '']
    number = 0
    for key, title in SECTIONS.items():
        if not ideas['sections'][key]:
            continue
        number += 1
        lines += [f'### {number}. {title}', '']
        for item in ideas['sections'][key]:
            refs = ', '.join(f'{sid} [{timestamp(ids[sid]["start"])}]' for sid in item['evidence'])
            label = 'Inferred suggestion/implication' if item['kind'] == 'inferred' else 'Expressed in recording'
            lines.append(f'- {item["text"]} ({label}; evidence: {refs})')
        lines.append('')
    return '\n'.join(lines)

