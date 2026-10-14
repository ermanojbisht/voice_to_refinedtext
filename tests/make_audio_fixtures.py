"""Generate reproducible annotated speech locally; never use microphone audio."""
import json
from pathlib import Path
import subprocess
import wave
import shutil


def generate(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    phrases = {
        'first': 'The bridge inspection is delayed. We should schedule a site visit on Friday.',
        'tail': 'The final action is to verify the budget of one hundred twenty three lakh rupees.',
        'hindi': 'सड़क का निरीक्षण पूरा हो गया है। पुल की मरम्मत जरूरी है। अगले सप्ताह बैठक करें।',
    }
    for name, text in phrases.items():
        # espeak Hindi has poor phoneme quality. Use an existing neural voice
        # when available; this is synthesis to a test file, never speaker output.
        voice = Path(__file__).parents[1] / 'models/hi_IN-priyamvada-medium.onnx'
        if name == 'hindi' and shutil.which('piper') and voice.is_file():
            subprocess.run(['piper', '--model', str(voice), '--noise-scale', '0', '--noise-w-scale', '0',
                            '--length-scale', '1.2', '--output_file', str(directory / f'{name}.wav')],
                           input=text, text=True, check=True)
            continue
        subprocess.run(['espeak-ng', '-v', 'hi' if name == 'hindi' else 'en-us', '-s', '145',
                        '-w', str(directory / f'{name}.wav'), text], check=True)
    with wave.open(str(directory / 'first.wav')) as first, wave.open(str(directory / 'tail.wav')) as last:
        rate = first.getframerate()
        data = first.readframes(first.getnframes())
        start_last = len(data) / 2 / rate + 16
        with wave.open(str(directory / 'long_pause.wav'), 'wb') as out:
            out.setparams(first.getparams())
            out.writeframes(data + b'\0\0' * (rate * 16) + last.readframes(last.getnframes()))
    annotations = {'phrases': phrases, 'long_pause': {'first_start': 0, 'tail_start': start_last,
                   'silent_gap_seconds': 16, 'critical_words': ['bridge', 'inspection', 'budget']}}
    (directory / 'annotations.json').write_text(json.dumps(annotations, ensure_ascii=False, indent=2))
    return annotations


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    generate(parser.parse_args().directory)

