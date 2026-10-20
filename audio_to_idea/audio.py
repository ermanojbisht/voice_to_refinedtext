"""Decode into unique temporary PCM files without shortening the timeline."""
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import wave

from .schemas import AudioToIdeaError, check_cancel

EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.webm'}


def command(args, cancel=None):
    """Bounded cancellation for FFmpeg; never pass file names through a shell."""
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        raise AudioToIdeaError(f'Cannot start {args[0]}: {exc}') from exc
    try:
        while True:
            check_cancel(cancel)
            try:
                out, err = proc.communicate(timeout=.2)
                break
            except subprocess.TimeoutExpired:
                continue
        if proc.returncode:
            raise AudioToIdeaError(f'{args[0]} failed: {err.decode(errors="replace")[-1600:]}')
        return out
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()


def probe(path, cancel=None):
    path = Path(path)
    if path.suffix.lower() not in EXTENSIONS or not path.is_file():
        raise AudioToIdeaError(f'Choose a readable audio file ({", ".join(sorted(EXTENSIONS))}): {path}')
    try:
        info = json.loads(command(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                                   '-of', 'json', str(path)], cancel))
        stream = next(s for s in info['streams'] if s['codec_type'] == 'audio')
        return {'duration': float(stream.get('duration') or info['format'].get('duration') or 0),
                'sample_rate': int(stream.get('sample_rate', 0)), 'channels': stream.get('channels', 0)}
    except (ValueError, KeyError, StopIteration) as exc:
        raise AudioToIdeaError(f'No decodable audio stream in {path}') from exc


def prepare(source, directory, settings, cancel=None):
    probe(source, cancel)
    target = Path(directory) / 'prepared.wav'
    args = ['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(source), '-map', '0:a:0', '-vn']
    if settings['normalize']:
        args += ['-af', f'loudnorm=I={settings["target_lufs"]}:TP={settings["true_peak_db"]}:LRA=11']
    args += ['-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(target)]
    command(args, cancel)
    with wave.open(str(target), 'rb') as handle:
        duration = handle.getnframes() / handle.getframerate()
    if duration <= 0:
        raise AudioToIdeaError('Audio contains no samples.')
    return target, duration


@dataclass(frozen=True)
class Chunk:
    index: int
    start: float
    end: float


def chunks(duration, seconds=60.0, overlap=1.5):
    """Sample-aligned windows, including the final tail, without a cross-fade."""
    length, shared = round(seconds * 16000), round(overlap * 16000)
    total = round(duration * 16000)
    if length <= shared or length < 16000 or shared < 0:
        raise AudioToIdeaError('Invalid chunk size/overlap.')
    start, index = 0, 0
    while start < total:
        end = min(start + length, total)
        yield Chunk(index, start / 16000, end / 16000)
        if end == total:
            break
        start += length - shared
        index += 1


def pause_guided_chunks(prepared_wav_path, target_seconds=None, min_chunk_seconds=None, max_chunk_seconds=None, min_pause_ms=None):
    """Generates audio_to_idea.audio.Chunk objects aligned with natural breath pauses using PauseGuidedChunker."""
    from audio_toolkit.chunker import PauseGuidedChunker
    chunker = PauseGuidedChunker(
        target_chunk_s=target_seconds,
        min_chunk_s=min_chunk_seconds,
        max_chunk_s=max_chunk_seconds,
        min_pause_ms=min_pause_ms,
    )
    audio_chunks = chunker.chunk_audio(str(prepared_wav_path))
    for ac in audio_chunks:
        yield Chunk(ac.index, round(ac.start_s, 3), round(ac.end_s, 3))


def samples(path, chunk):
    import numpy as np
    with wave.open(str(path), 'rb') as handle:
        rate = handle.getframerate()
        handle.setpos(round(chunk.start * rate))
        raw = handle.readframes(round((chunk.end - chunk.start) * rate))
    return np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768.0

