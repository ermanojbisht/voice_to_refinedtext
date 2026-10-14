"""Stable-file polling with bounded retry; generated artifacts are excluded."""
from pathlib import Path
import time

from .jobs import destination, inputs
from .schemas import AudioToIdeaError, check_cancel


class Watcher:
    def __init__(self, service, folder, output=None, summary=True, context='', profile=None, notify=None):
        self.service = service
        self.folder = Path(folder).expanduser().resolve()
        if not self.folder.is_dir():
            raise AudioToIdeaError('Watch input must be a folder.')
        self.output, self.summary, self.context, self.profile = output, summary, context, profile
        self.notify = notify or (lambda event: None)
        self.observed, self.done, self.attempts, self.retry_at = {}, {}, {}, {}

    def scan(self, cancel=None, now=None):
        """Injectable monotonic time makes slow-copy/backoff tests deterministic."""
        now = time.monotonic() if now is None else now
        cfg = self.service.settings['watch']
        results = []
        current_paths = inputs(self.folder, recursive=cfg['recursive'])
        for path in current_paths:
            check_cancel(cancel)
            stat = path.stat()
            identity = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
            previous = self.observed.get(path)
            if previous is None or previous[0] != identity:
                self.observed[path] = (identity, now)
                self.attempts[path] = 0
                self.retry_at[path] = 0
                continue
            if (self.done.get(path) == identity or now - previous[1] < cfg['stable_seconds']
                or self.attempts[path] >= 3 or now < self.retry_at[path]):
                continue
            output, name = destination(path, self.folder, self.output)
            result = self.service.run(path, output=output, name=name, summary=self.summary, context=self.context,
                                      profile=self.profile, cancel=cancel, notify=self.notify)
            results.append(result)
            self.attempts[path] += 1
            if result['status'] == 'complete':
                self.done[path] = identity
            else:
                self.retry_at[path] = now + min(300, 2 ** self.attempts[path] * cfg['poll_seconds'])
                if self.attempts[path] >= 3:
                    self.notify({'stage': 'warning', 'message': f'{path.name}: three failures; paused until file changes or watcher restarts'})
        for path in set(self.observed) - set(current_paths):
            self.observed.pop(path, None)
            self.done.pop(path, None)
            self.attempts.pop(path, None)
            self.retry_at.pop(path, None)
        return results

    def run(self, cancel):
        while not cancel.is_set():
            self.scan(cancel)
            cancel.wait(self.service.settings['watch']['poll_seconds'])

