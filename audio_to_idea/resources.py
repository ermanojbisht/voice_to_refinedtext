"""Cross-process inference coordination; microphone activity never blocks.

GPU residency is separate from locking: this module never unloads a model that
belongs to another process. Batch callers must release their own ASR instances.
"""
from contextlib import contextmanager
from functools import wraps
import os
from pathlib import Path
import tempfile
import threading
import time

from .schemas import AudioToIdeaError, check_cancel
from .storage import file_lock


def resource_dir():
    identity = str(os.getuid()) if hasattr(os, 'getuid') else os.environ.get('USERNAME', 'user')
    path = Path(os.environ.get('AUDIO2IDEA_RESOURCE_DIR', Path(tempfile.gettempdir()) / f'audio2idea-{identity}'))
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def process_birth(pid):
    """Linux start-time identity prevents stale markers surviving PID reuse."""
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    except (OSError, IndexError):
        return ''


def live_busy():
    for marker in resource_dir().glob('live-*'):
        try:
            pid = int(marker.name.split('-')[1])
            os.kill(pid, 0)
            birth = marker.read_text()
            if birth and birth != process_birth(pid):
                marker.unlink(missing_ok=True)
                continue
            return True
        except ProcessLookupError:
            marker.unlink(missing_ok=True)
        except (ValueError, PermissionError):
            return True
        except FileNotFoundError:
            continue
    return False


@contextmanager
def inference(cancel=None, batch=False, policy='queue', notify=None):
    """Legacy requests get priority over the next batch chunk, not preemption."""
    notified = False
    while True:
        check_cancel(cancel)
        if batch and live_busy():
            if policy != 'queue':
                raise AudioToIdeaError('Live recording is active; retry after it completes.')
            if notify and not notified:
                notify({'stage': 'waiting', 'message': 'Waiting for live recording to finish'})
                notified = True
            cancel.wait(.1) if cancel else time.sleep(.1)
            continue
        with file_lock(resource_dir() / 'inference.lock', cancel, wait=policy != 'error'):
            # A recording may have started between the first check and the lock.
            if batch and live_busy():
                continue
            yield
            return


def legacy_recording(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        marker = resource_dir() / f'live-{os.getpid()}-{threading.get_ident()}-recording'
        marker.write_text(process_birth(os.getpid()))
        try:
            return fn(*args, **kwargs)
        finally:
            marker.unlink(missing_ok=True)
    return wrapped


def legacy_inference(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        # Announce a waiting legacy request as well as an active one, preventing
        # a fast batch worker from repeatedly reacquiring the lock ahead of it.
        marker = resource_dir() / f'live-{os.getpid()}-{threading.get_ident()}-inference'
        marker.write_text(process_birth(os.getpid()))
        try:
            with inference():
                return fn(*args, **kwargs)
        finally:
            marker.unlink(missing_ok=True)
    return wrapped

