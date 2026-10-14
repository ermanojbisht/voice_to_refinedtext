"""Conservative overlap merging; raw chunk hypotheses remain available.

Duplicate removal requires both matching tokens and overlapping source-time
intervals from different chunks. Adjacent genuine repetitions are preserved.
"""
import re


def normalized(text):
    return re.sub(r'[^\w]', '', text, flags=re.UNICODE).casefold()


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
                         'text': ''.join(w['text'] for w in group['words']).strip(),
                         'words': [{k: v for k, v in w.items() if k not in {'chunk', 'group'}} for w in group['words']]})
    segments.sort(key=lambda s: (s['start'], s['end']))
    for i, seg in enumerate(segments, 1):
        seg['id'] = f'S{i:05d}'
    return segments, sorted(set(warnings))

