"""Conservative overlap merging; raw chunk hypotheses remain available.

Duplicate removal requires both matching tokens and overlapping source-time
intervals from different chunks. Adjacent genuine repetitions are preserved.
"""
import re


def normalized(text):
    return re.sub(r'[^\w]', '', text, flags=re.UNICODE).casefold()


def join_words(words_list):
    """Reconstructs text from word tokens safely.
    
    Handles both Whisper-style tokens (which may include leading spaces) and
    standard words / GGML tokens (which do not have leading spaces). Also prevents
    unwanted spaces before common punctuation marks.
    """
    if not words_list:
        return ""
    parts = []
    trailing_punct = {".", ",", "!", "?", ";", ":", ")", "]", "}", "%", "”", "’", "।", "॥"}
    leading_punct = {"(", "[", "{", "“", "‘", "$", "#", "@"}
    for i, w in enumerate(words_list):
        wt = (w.get("text") or "") if isinstance(w, dict) else getattr(w, "text", "")
        if not wt:
            continue
        if i > 0 and parts:
            prev = parts[-1]
            if not wt.startswith(" ") and not prev.endswith(" "):
                if wt not in trailing_punct and prev not in leading_punct:
                    parts.append(" ")
        parts.append(wt)
    return "".join(parts).strip()


def merge_chunks(results, duration):
    segments, words, warnings = [], [], []
    for chunk in results:
        for seg_index, seg in enumerate(chunk['segments']):
            if not seg['text'].strip():
                continue
            if seg.get('words'):
                for word in seg['words']:
                    start, end = max(0, word['start']), min(duration, word['end'])
                    if end < start:
                        continue
                    duplicate = False
                    for prev in reversed(words):
                        if prev['end'] < start - 2:
                            break
                        overlap = min(end, prev['end']) - max(start, prev['start'])
                        if (prev['chunk'] != chunk['index'] and overlap > 0 and
                            normalized(prev['text']) == normalized(word['text']) and
                            abs(prev['start'] - start) < .6):
                            duplicate = True
                            break
                    if not duplicate:
                        words.append({**word, 'start': start, 'end': end, 'chunk': chunk['index'], 'group': seg_index})
            else:
                item = {**seg, 'start': max(0, seg['start']), 'end': min(duration, seg['end'])}
                duplicate = any(normalized(item['text']) == normalized(p['text']) and
                                min(item['end'], p['end']) - max(item['start'], p['start']) >
                                .7 * max(.01, min(item['end'] - item['start'], p['end'] - p['start'])) for p in segments)
                if not duplicate:
                    segments.append(item)
                if chunk['index'] > 0:
                    warnings.append('Word timing unavailable at a chunk boundary; review overlap text.')
    words.sort(key=lambda w: (w['start'], w['end']))
    grouped = []
    for word in words:
        key = (word['chunk'], word['group'])
        if grouped and grouped[-1]['key'] == key:
            grouped[-1]['words'].append(word)
            grouped[-1]['end'] = max(grouped[-1]['end'], word['end'])
        else:
            grouped.append({'key': key, 'start': word['start'], 'end': word['end'], 'words': [word]})
    for group in grouped:
        segments.append({'start': group['start'], 'end': group['end'],
                         'text': join_words(group['words']),
                         'words': [{k: v for k, v in w.items() if k not in {'chunk', 'group'}} for w in group['words']]})
    segments.sort(key=lambda s: (s['start'], s['end']))
    for i, seg in enumerate(segments, 1):
        seg['id'] = f'S{i:05d}'
    return segments, sorted(set(warnings))

