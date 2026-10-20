# Unified Hotkey & Walkie-Talkie System: Architecture & Operations Guide

## 1. Overview & Core Concept

This system provides a unified **Hold-or-Toggle** hotkey mechanism for voice dictation on Linux (Ubuntu 22.04 through 26.04, Wayland and X11).

Instead of requiring separate keyboard shortcuts for push-to-talk versus toggle dictation, the **exact same key combination** (`GLOBAL_HOTKEY`, default `Ctrl+Space`) intuitively handles both:

| User Action | Interaction Type | Behavior | Best Used For |
| :--- | :--- | :--- | :--- |
| **Quick Tap** (`< 300ms`) | **Toggle Lock** | Tap once $\rightarrow$ starts continuous recording until you tap again or until silence triggers. | Long dictations, multi-paragraph notes, thoughts |
| **Press & Hold** (`> 300ms`) | **Push-to-Talk (Walkie-Talkie)** | Dictate while holding the key down $\rightarrow$ releasing the key immediately stops recording and auto-pastes. | Quick 1-sentence replies, commands, search queries |

If you change `GLOBAL_HOTKEY` in settings (e.g. from `Ctrl+Space` to `Ctrl+Alt+V`), **both behaviors automatically move together to the new key combination**.

---

## 2. Technical Architecture: How Wayland & Linux Are Solved

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Physical Hardware Keyboard                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Linux Kernel (/dev/input/event*)
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │             audio_toolkit/evdev_listener.py             │
       ├─────────────────────────────────────────────────────────┤
       │ • Reads raw kernel events directly (bypassing Wayland) │
       │ • value == 1 (Physical Press)   ──► coordinator.down()  │
       │ • value == 2 (OS Auto-repeat)   ──► SILENTLY IGNORED!   │
       │ • value == 0 (Physical Release) ──► coordinator.up()    │
       └────────────────────────────┬────────────────────────────┘
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │     audio_toolkit/hotkey_coordinator.py (Hold-or-Toggle)│
       ├─────────────────────────────────────────────────────────┤
       │ • If release arrives < 300ms  ──► LOCKS recording on    │
       │ • If release arrives > 300ms  ──► WAITS 50ms GRACE      │
       │ • If 50ms grace expires       ──► STOPS & AUTO-PASTES   │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │            tray_app.py / VoiceEngine Pipeline           │
       │        Record ──► Transcribe ──► Refine ──► Auto-Paste  │
       └─────────────────────────────────────────────────────────┘
```

### Why Standard Wayland Shortcuts Fail for Walkie-Talkie
1. **Wayland Security Isolation**: Wayland compositors intentionally block background applications from sniffing global keyboard releases.
2. **The GNOME `media-keys` Limitation**:
   - GNOME custom shortcuts (`org.gnome.settings-daemon.plugins.media-keys`) trigger only when a key is **pressed** (`pkill -USR1 -f tray_app.py`).
   - GNOME has **no event for key release**.
   - Furthermore, when holding a key, GNOME's desktop keyboard repeat repeatedly executes `pkill -USR1` every 250ms, causing rapid start/stop toggling that kills recordings prematurely.

### The Solution: Multi-Layer Resilience
1. **Kernel-Level `evdev` Listener (`audio_toolkit/evdev_listener.py`)**:
   - Directly monitors physical keyboards via `/dev/input/event*`.
   - Excludes virtual injection devices (e.g. `ydotoold`).
   - Distinguishes physical press (`1`), auto-repeat (`2`), and physical release (`0`).
   - Silently drops `value == 2` so OS auto-repeat never interrupts recording.
2. **Release Grace Window (`RELEASE_GRACE` = 50ms)**:
   - When a key release is received, the coordinator holds a 50ms grace timer. If synthetic key bounce or auto-repeat arrives within 50ms, the release is cancelled and recording continues seamlessly.
3. **External Signal Debounce Guard**:
   - In `HotkeyCoordinator.on_external_trigger()`, any incoming `SIGUSR1` that arrives within 800ms of recording start is safely ignored, preventing external auto-repeat loops.

---

## 3. Configuration & Web Settings

All parameters are configurable without editing code:

### Via Web Settings GUI
1. Open **[http://127.0.0.1:8765](http://127.0.0.1:8765)**.
2. Go to the **⚡ Auto-Paste & Desktop** tab.
3. Look for the **🎙️ Unified Hotkey & Walkie-Talkie Activation** section:
   - **Shortcut Activation Style (`SHORTCUT_ACTIVATION`)**:
     - `⚡ Hold-or-Toggle (Walkie-Talkie & Tap)` *(Recommended)*
     - `🔁 Toggle Only (Classic tap to start, tap to stop)`
     - `📻 Push-to-Talk Only (Hold key while speaking)`
   - **Walkie-Talkie Hold Threshold (`HOLD_THRESHOLD_MS`)**:
     - Slider from 150ms to 800ms (Default: `300ms`).
4. Click **Save Settings** (app auto-syncs dynamically).

### Via `config.json`
```json
{
    "GLOBAL_HOTKEY": "Ctrl+Space",
    "SHORTCUT_ACTIVATION": "hold_or_toggle",
    "HOLD_THRESHOLD_MS": 300,
    "RELEASE_GRACE_MS": 50
}
```

---

## 4. System Permissions & Requirements

### Linux User Permissions (`input` Group)
For `evdev` to read raw kernel keyboard events directly from `/dev/input/event*`, your Linux user must be in the `input` group:

```bash
# Check if your user is in the 'input' group
groups | grep input

# If not, add your user to the group:
sudo usermod -aG input $USER
```
*(Note: A one-time logout and login is required after adding a user to a group).*

### Fallback Behavior
If run in an environment where `/dev/input` permissions are restricted:
- The system gracefully logs:
  `Evdev hardware listener not available (using standard user-space fallback)`
- It transparently falls back to `pynput` and GNOME `SIGUSR1` toggle mode with the 800ms auto-repeat guard active.

---

## 5. Verification & Testing

Unit tests for all hotkey components are available in the test suite:

```bash
# Run all hotkey and evdev test suites
./.venv/bin/python -m pytest tests/test_hotkey_coordinator.py tests/test_evdev_listener.py tests/test_hotkey_management.py
```

### Verified Test Cases:
- `test_quick_tap_locks_recording`: Press + release at 80ms locks continuous recording; second press stops.
- `test_press_and_hold_walkie_talkie`: Press + hold for 400ms + release stops recording after grace.
- `test_x11_autorepeat_cancelled`: Synthetic key bounce within 50ms does not stop recording.
- `test_external_trigger_toggle`: SIGUSR1 toggles cleanly with 800ms auto-repeat protection.
- `test_parse_hotkey_ctrl_space`: Validates translation to Linux kernel `ecodes`.
- `test_evdev_mock_state_logic`: Verifies physical modifier matching and release detection.

---

## 6. Real-World Trial & Error Findings (Root Causes & Solutions)

During real-world hardware testing on Ubuntu 26.04 Wayland, two critical failure modes were discovered and permanently solved. These findings are documented here for future maintainers:

### Finding A: The "Voice Too Quiet / Nearly Silent" False Rejection
* **Symptom**: Holding down the hotkey to dictate resulted in an error notification: *"Recording too quiet — please try again"*, even though the user spoke at normal volume into a working microphone.
* **Root Cause**:
  - The application uses an audio quality safety gate (`_check_audio_quality()` in `tray_app.py`) to prevent transcribing dead mic silence:
    $$\text{Threshold} = \text{SILENCE\_THRESHOLD} \times \text{\_AUDIO\_QUALITY\_RATIO}$$
  - In `config.json`, `SILENCE_THRESHOLD` was set to `780`, and `_AUDIO_QUALITY_RATIO` was `0.5`, resulting in:
    $$\text{Threshold} = 780 \times 0.5 = 390.0\text{ RMS}$$
  - Normal, clear conversational human speech into standard USB and desktop microphones typically measures between **120 and 250 RMS**.
  - Because `174.5 RMS < 390.0 RMS`, the quality gate misclassified legitimate speech as background noise and aborted transcription!
* **Permanent Solution**:
  1. Updated `SILENCE_THRESHOLD` in `config.json` to `250`.
  2. Tuned `_AUDIO_QUALITY_RATIO` in `tray_app.py` to `0.25`:
     $$\text{Effective Threshold} = 250 \times 0.25 = 62.5\text{ RMS}$$
  3. This ensures true silence/dead mic ($0.0\text{ RMS}$) is still safely blocked, while natural conversational speech ($120\text{--}250\text{ RMS}$) is captured flawlessly.

### Finding B: Triple-Listener Signal Collision (Instant 0.05s Cutoff)
* **Symptom**: Holding `Ctrl+Space` started recording, but the application immediately cut off and stopped within 50 milliseconds (`STOP_RECORDING`).
* **Root Cause**:
  - On Ubuntu Wayland, three independent subsystems were simultaneously listening to `Ctrl+Space`:
    1. **`evdev`**: Physical kernel input listener in `audio_toolkit/evdev_listener.py`.
    2. **`pynput`**: User-space X11 listener in `tray_app.py`.
    3. **GNOME Shell**: Custom shortcut (`custom0`) executing `pkill -USR1 -f tray_app.py`.
  - When the user pressed `Ctrl+Space`:
    - `evdev` received the physical key-down first and dispatched `START_RECORDING`.
    - ~30ms later, `pynput` or GNOME's `SIGUSR1` arrived at the coordinator while `stage == RECORDING`.
    - Because the coordinator saw a second incoming hotkey event while already recording, it interpreted it as a second tap to stop, instantly killing the recording!
* **Permanent Solution (Exclusive Listener Ownership)**:
  1. In `tray_app.py`, `pynput`'s `on_press` and `on_release` now check `if not getattr(self, "_evdev_listener", None):`. When `evdev` is active, `pynput` mutes duplicate triggers for `GLOBAL_HOTKEY`.
  2. In `tray_app.py`, `handle_sigusr1()` checks `if getattr(self, "_evdev_listener", None):` and safely ignores duplicate GNOME shell signals.
  3. `evdev` is granted **exclusive ownership** of the hotkey lifecycle, allowing holds and releases to be tracked with pure hardware accuracy.
