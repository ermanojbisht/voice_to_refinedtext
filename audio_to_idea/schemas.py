"""Shared errors and cancellation contracts for CLI, GUI and workers."""
import threading


class AudioToIdeaError(Exception):
    """An actionable processing/configuration error safe to show in the UI."""


class Cancelled(AudioToIdeaError):
    """The caller requested cancellation; already durable stages remain valid."""


def check_cancel(event: threading.Event | None):
    if event is not None and event.is_set():
        raise Cancelled('Cancelled; completed stages are saved for the next run.')

