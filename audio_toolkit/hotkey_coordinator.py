"""audio_toolkit/hotkey_coordinator.py.

Unified Hold-or-Toggle (Walkie-Talkie & Tap) Hotkey Coordinator (Track D - TODO-D2).
Ported and adapted from Handy's transcription_coordinator.rs.

Features:
1. Single Hotkey Dual Interaction:
   - Quick Tap (< 300ms): Locks session into continuous recording (Tap to start, Tap to stop).
   - Press & Hold (> 300ms): Walkie-talkie / push-to-talk. Releasing stops recording immediately.
2. Linux Auto-Repeat Resilience:
   - 50ms RELEASE_GRACE window cancels synthetic X11/Wayland auto-repeat releases during long holds.
3. Decoupled State Machine:
   - Emits pure CoordinatorEffect actions (START_RECORDING, STOP_RECORDING).
   - Seamlessly accepts dynamic runtime reconfiguration of hotkey, activation mode, and thresholds.
"""

from __future__ import annotations

import enum
import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ShortcutActivation(str, enum.Enum):
    HOLD_OR_TOGGLE = "hold_or_toggle"
    TOGGLE = "toggle"
    PUSH_TO_TALK = "push_to_talk"


class CoordinatorStage(str, enum.Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


class CoordinatorEffect(str, enum.Enum):
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    NO_OP = "no_op"


class PendingRelease:
    """Represents a key-up event deferred by RELEASE_GRACE."""

    def __init__(self, released_at: float, deadline: float, hold_threshold: float):
        self.released_at = released_at
        self.deadline = deadline
        self.hold_threshold = hold_threshold


class HotkeyCoordinator:
    """Manages the lifecycle state transitions for unified hotkeys."""

    def __init__(
        self,
        mode: str = "hold_or_toggle",
        hold_threshold_ms: int = 300,
        release_grace_ms: int = 50,
        on_effect: Optional[Callable[[CoordinatorEffect], None]] = None,
    ):
        self._lock = threading.RLock()
        self.mode = ShortcutActivation(mode.lower()) if mode else ShortcutActivation.HOLD_OR_TOGGLE
        self.hold_threshold = max(0.05, float(hold_threshold_ms) / 1000.0)
        self.release_grace = max(0.01, float(release_grace_ms) / 1000.0)
        self.on_effect = on_effect

        self.stage = CoordinatorStage.IDLE
        self.is_locked = False
        self.pressed_at: Optional[float] = None
        self.last_press_time: float = 0.0

        self.pending_release: Optional[PendingRelease] = None
        self._grace_timer: Optional[threading.Timer] = None

    def set_mode(self, mode: str) -> None:
        with self._lock:
            try:
                self.mode = ShortcutActivation(mode.lower())
                logger.info("HotkeyCoordinator mode set to %s", self.mode.value)
            except ValueError:
                self.mode = ShortcutActivation.HOLD_OR_TOGGLE

    def set_hold_threshold_ms(self, ms: int) -> None:
        with self._lock:
            self.hold_threshold = max(0.05, float(ms) / 1000.0)

    def set_release_grace_ms(self, ms: int) -> None:
        with self._lock:
            self.release_grace = max(0.01, float(ms) / 1000.0)

    # ── Input Handlers ───────────────────────────────────────────────────────

    def on_hotkey_down(self, now: Optional[float] = None) -> CoordinatorEffect:
        """Called when the configured hotkey combination transitions to pressed."""
        with self._lock:
            t = time.time() if now is None else now

            # 1. Debounce rapid identical presses (30ms)
            if (t - self.last_press_time) < 0.030:
                return CoordinatorEffect.NO_OP
            self.last_press_time = t

            # 2. Check if a release grace was pending
            if self.pending_release is not None:
                # Synthetic auto-repeat press or user tapped again within 50ms: cancel release
                self._cancel_grace_timer()
                self.pending_release = None
                logger.debug("HotkeyCoordinator: Synthetic repeat detected; cancelled deferred release")
                return CoordinatorEffect.NO_OP

            # 3. Handle by stage
            if self.stage == CoordinatorStage.IDLE:
                self.pressed_at = t
                if self.mode == ShortcutActivation.TOGGLE:
                    self.is_locked = True
                else:
                    self.is_locked = False

                self.stage = CoordinatorStage.RECORDING
                effect = CoordinatorEffect.START_RECORDING
                self._dispatch(effect)
                return effect

            elif self.stage == CoordinatorStage.RECORDING:
                # If locked (session started via a quick tap or toggle mode), next press ends it
                if self.is_locked or self.mode == ShortcutActivation.TOGGLE:
                    self.stage = CoordinatorStage.PROCESSING
                    effect = CoordinatorEffect.STOP_RECORDING
                    self._dispatch(effect)
                    return effect
                else:
                    # Key is still held down in walkie-talkie mode; ignore repeated press
                    return CoordinatorEffect.NO_OP

            elif self.stage == CoordinatorStage.PROCESSING:
                # Pipeline is busy processing previous utterance; ignore
                return CoordinatorEffect.NO_OP

            return CoordinatorEffect.NO_OP

    def on_hotkey_up(self, now: Optional[float] = None) -> CoordinatorEffect:
        """Called when the trigger key or primary modifier of the hotkey is released."""
        with self._lock:
            t = time.time() if now is None else now

            # If not recording or in pure toggle mode, release has no effect
            if self.stage != CoordinatorStage.RECORDING:
                return CoordinatorEffect.NO_OP

            if self.mode == ShortcutActivation.TOGGLE:
                return CoordinatorEffect.NO_OP

            # If already locked into continuous recording (e.g. earlier tap was resolved), ignore release
            if self.is_locked:
                return CoordinatorEffect.NO_OP

            # In hold modes (HOLD_OR_TOGGLE or PUSH_TO_TALK):
            # Defer release by RELEASE_GRACE to absorb synthetic X11/Wayland auto-repeats
            effective_threshold = 0.0 if self.mode == ShortcutActivation.PUSH_TO_TALK else self.hold_threshold
            deadline = t + self.release_grace

            self.pending_release = PendingRelease(
                released_at=t,
                deadline=deadline,
                hold_threshold=effective_threshold,
            )

            self._cancel_grace_timer()
            self._grace_timer = threading.Timer(self.release_grace, self._on_grace_expired)
            self._grace_timer.daemon = True
            self._grace_timer.start()
            return CoordinatorEffect.NO_OP

    def on_external_trigger(self, now: Optional[float] = None) -> CoordinatorEffect:
        """Called on external edge triggers (e.g. SIGUSR1, CLI toggle flag).

        These must never be debounced and strictly toggle recording state.
        """
        with self._lock:
            t = time.time() if now is None else now
            self._cancel_grace_timer()
            self.pending_release = None

            if self.stage == CoordinatorStage.IDLE:
                self.stage = CoordinatorStage.RECORDING
                self.is_locked = True
                self.pressed_at = t
                effect = CoordinatorEffect.START_RECORDING
                self._dispatch(effect)
                return effect
            elif self.stage == CoordinatorStage.RECORDING:
                self.stage = CoordinatorStage.PROCESSING
                self.is_locked = False
                effect = CoordinatorEffect.STOP_RECORDING
                self._dispatch(effect)
                return effect
            else:
                return CoordinatorEffect.NO_OP

    # ── Grace Resolution ─────────────────────────────────────────────────────

    def _on_grace_expired(self) -> None:
        with self._lock:
            if self.pending_release is None:
                return
            pending = self.pending_release
            self.pending_release = None

            if self.stage != CoordinatorStage.RECORDING:
                return

            held_duration = pending.released_at - (self.pressed_at or pending.released_at)

            if held_duration < pending.hold_threshold:
                # Key was tapped quickly (< hold_threshold) -> LOCK into continuous recording
                self.is_locked = True
                logger.debug(
                    "HotkeyCoordinator: Tap classified (held %.1fms < %.1fms) -> Session LOCKED on",
                    held_duration * 1000.0,
                    pending.hold_threshold * 1000.0,
                )
            else:
                # Key was held (> hold_threshold) -> Walkie-Talkie release -> STOP recording
                logger.debug(
                    "HotkeyCoordinator: Hold classified (held %.1fms >= %.1fms) -> Stopping recording",
                    held_duration * 1000.0,
                    pending.hold_threshold * 1000.0,
                )
                self.stage = CoordinatorStage.PROCESSING
                self.is_locked = False
                self._dispatch(CoordinatorEffect.STOP_RECORDING)

    def _cancel_grace_timer(self) -> None:
        if self._grace_timer is not None:
            try:
                self._grace_timer.cancel()
            except Exception:
                pass
            self._grace_timer = None

    # ── Pipeline Lifecycle Hooks ─────────────────────────────────────────────

    def notify_pipeline_finished(self) -> None:
        """Called when audio recording/processing has completed and system is ready for new input."""
        with self._lock:
            self._cancel_grace_timer()
            self.pending_release = None
            self.is_locked = False
            self.stage = CoordinatorStage.IDLE
            self.pressed_at = None

    def _dispatch(self, effect: CoordinatorEffect) -> None:
        if self.on_effect and effect != CoordinatorEffect.NO_OP:
            try:
                self.on_effect(effect)
            except Exception as e:
                logger.error("Error in HotkeyCoordinator callback: %s", e)
