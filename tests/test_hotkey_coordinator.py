"""tests/test_hotkey_coordinator.py.

Unit tests for HotkeyCoordinator (Track D - TODO-D2).
Verifies hold-or-toggle dual interaction, release grace, and auto-repeat absorption.
"""

import time
import pytest
from audio_toolkit.hotkey_coordinator import (
    HotkeyCoordinator,
    ShortcutActivation,
    CoordinatorStage,
    CoordinatorEffect,
)


def test_quick_tap_locks_recording():
    """Tapping < 300ms locks the recording on. Next tap stops it."""
    effects = []
    coordinator = HotkeyCoordinator(
        mode="hold_or_toggle",
        hold_threshold_ms=200,
        release_grace_ms=30,
        on_effect=lambda eff: effects.append(eff),
    )

    t0 = 100.0
    # 1. Tap down
    eff1 = coordinator.on_hotkey_down(now=t0)
    assert eff1 == CoordinatorEffect.START_RECORDING
    assert coordinator.stage == CoordinatorStage.RECORDING
    assert coordinator.is_locked is False

    # 2. Release quickly at 80ms (< 200ms threshold)
    eff2 = coordinator.on_hotkey_up(now=t0 + 0.08)
    assert eff2 == CoordinatorEffect.NO_OP

    # Wait for grace timer (30ms) to resolve the tap
    time.sleep(0.06)

    # Coordinator should now be locked on
    assert coordinator.stage == CoordinatorStage.RECORDING
    assert coordinator.is_locked is True

    # 3. Next tap down should stop recording
    eff3 = coordinator.on_hotkey_down(now=t0 + 1.0)
    assert eff3 == CoordinatorEffect.STOP_RECORDING
    assert coordinator.stage == CoordinatorStage.PROCESSING
    assert effects == [CoordinatorEffect.START_RECORDING, CoordinatorEffect.STOP_RECORDING]


def test_press_and_hold_walkie_talkie():
    """Holding > 300ms acts as walkie-talkie; release stops recording."""
    effects = []
    coordinator = HotkeyCoordinator(
        mode="hold_or_toggle",
        hold_threshold_ms=200,
        release_grace_ms=30,
        on_effect=lambda eff: effects.append(eff),
    )

    t0 = 100.0
    # 1. Press down
    eff1 = coordinator.on_hotkey_down(now=t0)
    assert eff1 == CoordinatorEffect.START_RECORDING

    # 2. Release after 400ms (> 200ms threshold)
    eff2 = coordinator.on_hotkey_up(now=t0 + 0.40)
    assert eff2 == CoordinatorEffect.NO_OP

    # Wait for grace timer (30ms)
    time.sleep(0.06)

    # Should have stopped recording
    assert coordinator.stage == CoordinatorStage.PROCESSING
    assert coordinator.is_locked is False
    assert effects == [CoordinatorEffect.START_RECORDING, CoordinatorEffect.STOP_RECORDING]


def test_x11_autorepeat_cancelled():
    """Synthetic release followed by immediate press within grace window does not stop recording."""
    effects = []
    coordinator = HotkeyCoordinator(
        mode="hold_or_toggle",
        hold_threshold_ms=200,
        release_grace_ms=50,
        on_effect=lambda eff: effects.append(eff),
    )

    t0 = 100.0
    # 1. Physical press down
    coordinator.on_hotkey_down(now=t0)

    # 2. Synthetic key-up at 300ms
    coordinator.on_hotkey_up(now=t0 + 0.30)
    assert coordinator.pending_release is not None

    # 3. Synthetic key-down arrives at 320ms (within 50ms grace)
    eff_repeat = coordinator.on_hotkey_down(now=t0 + 0.32)
    assert eff_repeat == CoordinatorEffect.NO_OP
    # Grace timer should have been cancelled
    assert coordinator.pending_release is None

    # Wait 60ms past the original release deadline
    time.sleep(0.07)

    # Recording should STILL be active
    assert coordinator.stage == CoordinatorStage.RECORDING
    assert effects == [CoordinatorEffect.START_RECORDING]

    # 4. Eventual real release at 600ms
    coordinator.on_hotkey_up(now=t0 + 0.60)
    time.sleep(0.07)
    assert coordinator.stage == CoordinatorStage.PROCESSING
    assert effects == [CoordinatorEffect.START_RECORDING, CoordinatorEffect.STOP_RECORDING]


def test_toggle_mode_ignores_release():
    """In pure toggle mode, key releases never affect recording state."""
    effects = []
    coordinator = HotkeyCoordinator(
        mode="toggle",
        on_effect=lambda eff: effects.append(eff),
    )

    coordinator.on_hotkey_down()
    assert coordinator.stage == CoordinatorStage.RECORDING
    assert coordinator.is_locked is True

    # Release should be a complete no-op
    coordinator.on_hotkey_up()
    time.sleep(0.06)
    assert coordinator.stage == CoordinatorStage.RECORDING

    # Second press stops
    coordinator.on_hotkey_down(now=time.time() + 1.0)
    assert coordinator.stage == CoordinatorStage.PROCESSING
    assert effects == [CoordinatorEffect.START_RECORDING, CoordinatorEffect.STOP_RECORDING]


def test_push_to_talk_mode_stops_on_any_release():
    """In push-to-talk mode, even a short release stops recording."""
    effects = []
    coordinator = HotkeyCoordinator(
        mode="push_to_talk",
        release_grace_ms=20,
        on_effect=lambda eff: effects.append(eff),
    )

    coordinator.on_hotkey_down()
    # Release after only 50ms
    coordinator.on_hotkey_up()
    time.sleep(0.04)

    assert coordinator.stage == CoordinatorStage.PROCESSING
    assert effects == [CoordinatorEffect.START_RECORDING, CoordinatorEffect.STOP_RECORDING]


def test_external_trigger_toggle():
    """External triggers (SIGUSR1 / CLI) toggle recording cleanly without grace delay."""
    effects = []
    coordinator = HotkeyCoordinator(
        mode="hold_or_toggle",
        on_effect=lambda eff: effects.append(eff),
    )

    eff1 = coordinator.on_external_trigger()
    assert eff1 == CoordinatorEffect.START_RECORDING
    assert coordinator.stage == CoordinatorStage.RECORDING
    assert coordinator.is_locked is True

    eff2 = coordinator.on_external_trigger()
    assert eff2 == CoordinatorEffect.STOP_RECORDING
    assert coordinator.stage == CoordinatorStage.PROCESSING


def test_pipeline_reset():
    """notify_pipeline_finished resets coordinator to IDLE."""
    coordinator = HotkeyCoordinator()
    coordinator.on_hotkey_down()
    assert coordinator.stage == CoordinatorStage.RECORDING

    coordinator.notify_pipeline_finished()
    assert coordinator.stage == CoordinatorStage.IDLE
    assert coordinator.is_locked is False
