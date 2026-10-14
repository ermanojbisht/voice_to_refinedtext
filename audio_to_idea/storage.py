"""Atomic persistence and process locks, isolated from legacy review state."""
import contextlib
import errno
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from .schemas import AudioToIdeaError, check_cancel


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path, text):
    """Replace only after flush/fsync; failed writes leave the old file intact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '.', delete=False) as handle:
            name = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        if hasattr(os, 'O_DIRECTORY'):
            directory = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()


def write_json(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise AudioToIdeaError(f'Cannot read {path}: {exc}') from exc


@contextlib.contextmanager
def file_lock(path, cancel=None, wait=True, timeout=None):
    """Kernel lock ownership expires on process exit; the file itself may remain.

Never unlink a lock file: another waiter may hold its inode. Windows support is
kept here so core file processing need not import POSIX-only review code.
"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        started = time.monotonic()
        while True:
            check_cancel(cancel)
            try:
                if os.name == 'nt':
                    import msvcrt
                    handle.seek(0)
                    if not path.stat().st_size:
                        handle.write(b'0')
                        handle.flush()
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in {errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK}:
                    raise AudioToIdeaError(f'File locking is unavailable for {path}: {exc}') from exc
                if not wait or (timeout is not None and time.monotonic() - started >= timeout):
                    raise AudioToIdeaError(f'Another job is using this resource: {path.name}')
                if cancel:
                    cancel.wait(.1)
                else:
                    time.sleep(.1)
        try:
            yield
        finally:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_UN)

