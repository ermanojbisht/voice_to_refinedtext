from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest
from audio_to_idea.config import DEFAULTS
from audio_to_idea.jobs import JobService, destination
from audio_to_idea.resources import inference, legacy_inference, legacy_recording, live_busy, resource_dir
from audio_to_idea.schemas import AudioToIdeaError, Cancelled
from audio_to_idea.storage import atomic_write, file_lock, read_json, write_json
from audio_to_idea.watcher import Watcher
from test_audio_exports import wav
from test_config_models import model
from test_jobs_synthesis import FakeASR, FakeLLM


def test_chunk_crash_resume(tmp_path):
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    cfg['audio'].update(chunk_seconds=1, overlap_seconds=.1)
    source = wav(tmp_path / 'note.wav', seconds=3)
    seen = []
    class Crash(FakeASR):
        def transcribe(self, path, chunk, glossary):
            seen.append(chunk.index)
            if chunk.index == 1:
                raise AudioToIdeaError('Simulated interruption')
            return super().transcribe(path, chunk, glossary)
    first = JobService(cfg, Crash, FakeLLM).run(source, summary=False)
    assert first['status'] == 'failed' and seen == [0, 1]
    class Resume(FakeASR):
        def transcribe(self, path, chunk, glossary):
            seen.append(chunk.index)
            return super().transcribe(path, chunk, glossary)
    second = JobService(cfg, Resume, FakeLLM).run(source, summary=False)
    assert second['status'] == 'complete'
    assert seen == [0, 1, 1, 2, 3]
    assert read_json(Path(second['workspace']) / 'manifest.json')['status'] == 'complete'


def test_atomic_failure_preserves_old_content(tmp_path, monkeypatch):
    path = tmp_path / 'output.txt'
    path.write_text('old')
    def fail(*args):
        raise OSError('Simulated disk full')
    monkeypatch.setattr(os, 'replace', fail)
    with pytest.raises(OSError):
        atomic_write(path, 'new')
    assert path.read_text() == 'old'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['output.txt']


def test_cross_process_lock_owner_and_crash_release(tmp_path):
    lock = tmp_path / 'job.lock'
    code = 'from audio_to_idea.storage import file_lock; import sys;\nwith file_lock(sys.argv[1],wait=False): print("acquired")'
    with file_lock(lock):
        child = subprocess.run([sys.executable, '-c', code, str(lock)], capture_output=True, text=True)
        assert child.returncode != 0 and 'Another job' in child.stderr
    child = subprocess.run([sys.executable, '-c', code, str(lock)], capture_output=True, text=True)
    assert child.returncode == 0


def test_recording_priority_cancellation_and_marker_cleanup():
    entered = threading.Event()
    release = threading.Event()
    @legacy_recording
    def record():
        entered.set()
        release.wait(3)
    thread = threading.Thread(target=record)
    thread.start()
    assert entered.wait(1) and live_busy()
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(Cancelled):
        with inference(cancelled, batch=True):
            pytest.fail('Must not enter')
    with pytest.raises(AudioToIdeaError):
        with inference(batch=True, policy='error'):
            pytest.fail('Must not enter')
    release.set()
    thread.join()
    assert not live_busy()
    @legacy_inference
    def infer():
        assert live_busy()
        return 'unchanged'
    assert infer() == 'unchanged' and not live_busy()


def test_same_stem_extensions_and_nested_outputs(tmp_path):
    folder = tmp_path / 'input' / 'nested'
    folder.mkdir(parents=True)
    a, b = folder / 'same.wav', folder / 'same.mp3'
    a.touch(); b.touch()
    x = destination(a, tmp_path / 'input', tmp_path / 'out')
    y = destination(b, tmp_path / 'input', tmp_path / 'out')
    assert x[0] == y[0] == tmp_path / 'out' / 'nested'
    assert x[1] != y[1]


def test_watcher_bounded_retry(tmp_path):
    source = wav(tmp_path / 'note.wav')
    class Service:
        settings = deepcopy(DEFAULTS)
        calls = 0
        def run(self, *args, **kwargs):
            self.calls += 1
            return {'status': 'failed'}
    service = Service()
    watch = Watcher(service, tmp_path)
    for now in [0, 6, 7, 20, 50, 1000]:
        watch.scan(now=now)
    assert service.calls == 3


def test_headless_cli_json_help_and_invalid_config(tmp_path):
    env = {**os.environ, 'DISPLAY': '', 'WAYLAND_DISPLAY': ''}
    help_run = subprocess.run([sys.executable, '-m', 'audio_to_idea', '--help'], env=env, capture_output=True, text=True)
    assert help_run.returncode == 0 and 'process' in help_run.stdout
    cfg = tmp_path / 'config.json'
    write_json(cfg, DEFAULTS)
    check = subprocess.run([sys.executable, '-m', 'audio_to_idea', 'doctor', '--config', str(cfg),
                            '--cache-root', str(tmp_path / 'missing'), '--json'], env=env, capture_output=True, text=True)
    assert check.returncode == 2 and json.loads(check.stdout)['errors']
    code = 'import audio_to_idea.cli,sys; assert not any(x in sys.modules for x in ["pynput","sounddevice","tkinter","customtkinter","engine","review_engine"])'
    imported = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True)
    assert imported.returncode == 0, imported.stderr


def test_mixed_batch_continues_after_bad_audio(tmp_path, monkeypatch, capsys):
    import audio_to_idea.cli as cli
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    profile = tmp_path / 'settings.json'
    write_json(profile, cfg)
    folder = tmp_path / 'incoming'
    folder.mkdir()
    (folder / 'bad.wav').write_bytes(b'invalid WAV')
    wav(folder / 'good.wav')
    monkeypatch.setattr(cli, 'JobService', lambda c: JobService(c, FakeASR, FakeLLM))
    assert cli.main(['transcribe', '--config', str(profile), '-i', str(folder), '-o', str(tmp_path / 'out'), '--json']) == 3
    results = json.loads(capsys.readouterr().out)['results']
    assert [r['status'] for r in results] == ['failed', 'complete']


def test_future_manifest_preserved(tmp_path):
    from audio_to_idea.storage import fingerprint
    cfg = deepcopy(DEFAULTS)
    source = wav(tmp_path / 'note.wav')
    workspace = tmp_path / '.audio2idea' / fingerprint(str(source))[:20]
    manifest = workspace / 'manifest.json'
    write_json(manifest, {'version': 99, 'source': str(source), 'unknown_future_data': True})
    before = manifest.read_bytes()
    assert JobService(cfg, FakeASR, FakeLLM).run(source, summary=False)['status'] == 'failed'
    assert manifest.read_bytes() == before


def test_parallel_clients_reuse_one_transcription(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    source = wav(tmp_path / 'note.wav')
    before = FakeASR.calls
    service = JobService(cfg, FakeASR, FakeLLM)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(service.run, source, summary=False) for _ in range(2)]
        assert all(job.result()['status'] == 'complete' for job in jobs)
    assert FakeASR.calls - before == 1


def test_process_exit_releases_lock_and_resumes_checkpoint(tmp_path):
    """A real process exit bypasses finally; its completed chunk must survive."""
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    cfg['audio'].update(chunk_seconds=1, overlap_seconds=.1)
    source = wav(tmp_path / 'note.wav', seconds=3)
    settings = tmp_path / 'settings.json'
    write_json(settings, cfg)
    helpers = str(Path(__file__).parent)
    script = '''import json,os,sys
sys.path.insert(0,sys.argv[3])
from audio_to_idea.jobs import JobService
from test_jobs_synthesis import FakeASR,FakeLLM
def progress(event):
    if event.get('stage')=='transcription' and event.get('current')==2:
        os._exit(42)
JobService(json.load(open(sys.argv[1])),FakeASR,FakeLLM).run(sys.argv[2],summary=False,notify=progress)
'''
    child = subprocess.run([sys.executable, '-c', script, str(settings), str(source), helpers],
                           capture_output=True, text=True, timeout=30)
    assert child.returncode == 42, child.stderr
    before = FakeASR.calls
    result = JobService(cfg, FakeASR, FakeLLM).run(source, summary=False)
    assert result['status'] == 'complete', result
    assert FakeASR.calls - before == 3  # Four chunks; the child saved chunk zero.
