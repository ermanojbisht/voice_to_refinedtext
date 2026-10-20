"""Audio Toolkit package providing pre-speech ring buffering, neural VAD, pause-guided chunking, and safe clipboard pasting."""
from .ring_buffer import CircularAudioBuffer
from .silero_vad import SileroVAD
from .recorder import StreamRecorder
from .chunker import PauseGuidedChunker
from .clipboard import ClipboardManager, get_clipboard_manager, is_wayland
from .overlay import RecordingOverlay, get_recording_overlay
from .hotkey_coordinator import HotkeyCoordinator, ShortcutActivation, CoordinatorEffect
from .evdev_listener import EvdevHotkeyListener, parse_hotkey_to_evdev

__all__ = [
    "CircularAudioBuffer",
    "SileroVAD",
    "StreamRecorder",
    "PauseGuidedChunker",
    "ClipboardManager",
    "get_clipboard_manager",
    "is_wayland",
    "RecordingOverlay",
    "get_recording_overlay",
    "HotkeyCoordinator",
    "ShortcutActivation",
    "CoordinatorEffect",
    "EvdevHotkeyListener",
    "parse_hotkey_to_evdev",
]
