# Next-Level Animated Visuals, Icons & GUI Modernization — Architecture Plan

**Created:** 2026-10-19  
**Status:** In Review / Ready for Implementation  
**Target Environments:**
- Home PC: Ubuntu 26.04 LTS, Python 3.14, NVIDIA GeForce RTX 3060 12GB (Vulkan)
- Office PC: Ubuntu 22.04 LTS, Python 3.10, Low-VRAM / Shared GPU / CPU

---

## 1. Executive Summary & Design Vision

Voice dictation and local AI text refinement are tactile, real-time workflows. In applications like `cjpais/Handy`, the interface communicates clearly with expressive metaphors:
- **Listening / Recording**: An **Ear (👂) / Acoustic Soundwave** tells the user instantly that their microphone is live and capturing audio.
- **Thinking / Processing**: A **Brain (🧠) / Neural Synapse** tells the user that the AI is actively transcribing speech and running local LLM refinement.
- **Idle / Ready**: A sleek **Microphone (🎙)** or resting halo indicates the assistant is on standby.
- **Success / Copied**: A **Sparkle (✨)** or green checkmark confirms the text was placed into the clipboard.

In contrast, our system historically relied on static single-color dots (grey, red, blue circles). This document plans the next-level visual upgrade across:
1. **The Main GUI (`main_gui.py`)**: Dynamic animated canvas visualizer switching between Mic, Animated Ear/Soundwave, Animated Neural Brain, and Success states.
2. **The System Tray App (`tray_app.py`)**: High-dpi vector/Pillow status icons (Mic, Ear, Brain, Moon) with optional smooth frame animation during active recording and refinement.
3. **Settings & Controls GUI (`config_gui.py`)**: Modern Catppuccin glass card containers, dark input wells, and crisp typography.
4. **Optional Floating Mini HUD (`floating_hud.py`)**: A Handy-style lightweight desktop pill that appears on screen whenever voice recording begins and auto-dismisses when text is typed.

---

## 2. Visual Architecture & State Machines

### 2.1 State Matrix & Visual Metaphors

| State | Old Look | New Metaphor | Visual Animation Details |
|---|---|---|---|
| **IDLE** | Static grey dot | **Sleek Microphone 🎙** | Frosted glass ring with subtle ambient resting glow (30s breathing pulse). |
| **RECORDING** | Static red dot | **Listening Ear 👂 & Acoustic Wave** | Expanding concentric acoustic soundwaves pulsing with voice activity (33 FPS, mathematical sine modulation). |
| **TRANSCRIBING & REFINING** | Static yellow/blue dot | **Neural Brain 🧠 & AI Synapse** | Rotating neural orbit with glowing node points, visually representing local LLM reasoning and processing. |
| **SUCCESS** | Static green dot | **Sparkle ✨ & Checkmark** | Expanding emerald ripple confirming clipboard placement. |
| **EVENING REVIEW** | Static green dot | **Crescent Moon 🌙 / Journal** | Dedicated evening reflection badge. |

---

### 2.2 Subsystem Architectures

#### A. Main GUI Canvas Visualizer (`main_gui.py`)
- **Technology**: Native `tkinter.Canvas` with high-performance vector rendering.
- **Performance Budget**: 
  - < 0.5% CPU during animation.
  - 0% CPU when idle.
  - Zero external heavyweight dependencies (e.g., no PyGame or Chromium webviews).
- **Smoothness**: 30–33 FPS timer loop (`root.after(30, ...)`), active strictly while recording or processing.
- **Component Hierarchy**:
  - `Header`: App title, active profile pill (`nemotron_fast`), engine badge (`transcribe-cpp`), mode pill (`Refine` / `Translate`).
  - `Hero Card`: Rounded `CTkFrame` (`corner_radius=16`, `SURFACE` color, `BORDER` outline) containing the multi-state animated canvas, status header, hero action button, and progress indicator.
  - `Output Card`: Text container with header actions ("📋 Copy", character/word counter) and dark well text area.
  - `Footer`: Secondary actions with clean hover transitions.

#### B. System Tray Dynamic Icon Generator (`tray_app.py`)
- **Technology**: Programmatic Pillow RGBA drawing at 64x64 native resolution (crisp scaling on 100%, 150%, 200% DPI).
- **Icon Set**:
  - `mic_icon(color)`: Crisp geometric microphone with stand and base.
  - `ear_wave_icon(frame, color)`: Ear profile with radiating acoustic arc waves.
  - `brain_synapse_icon(frame, color)`: Neural lobes with orbiting synapse dots.
  - `moon_icon(color)`: Crescent moon for review mode.
- **Animation Loop**: When `self.is_recording` or `self.is_processing` is active, a dedicated daemon thread cycles 4–8 icon frames every 120ms (`self.icon.icon = frame`). Gracefully falls back to static crisp icons if the system tray daemon does not support rapid pixmap updates.

#### C. Settings GUI Modernization (`config_gui.py`)
- Standardized Card Layout:
  - Sections grouped into rounded `CTkFrame` cards (`SURFACE = "#2a2b3d"`, `BORDER = "#363a4f"`).
  - Inputs nested in dark well frames (`FIELD = "#181825"`).
  - High-contrast typography with Catppuccin accents (`ACCENT = "#89b4fa"`, `TEXT = "#cdd6f4"`, `MUTED = "#6c7086"`).
  - Fixed-height bottom action bar preserving all form state and keyboard shortcuts.

#### D. Optional Floating Mini-HUD (`floating_hud.py`)
- Lightweight `ctk.CTkToplevel` with `overrideredirect(True)` and `attributes("-topmost", True)`.
- Appears seamlessly on global hotkey press near screen center or bottom-right corner.
- Displays the live animated Ear during recording, switches to the Brain during LLM refinement, and fades out upon text insertion.

---

## 3. Compatibility & Quality Invariants

1. **Python Compatibility**:
   - Strictly compatible with Python 3.10 (Ubuntu 22.04 Office PC) through Python 3.14 (Ubuntu 26.04 Home PC).
   - Use `from __future__ import annotations`, avoid `match/case`, use union types with `typing.Union`.
2. **Display Server Neutrality**:
   - Works flawlessly under both **Wayland** (GNOME 46+) and **X11** (Xvfb / desktop).
   - Canvas coordinate transformations avoid floating point truncation issues.
3. **Zero Test Regressions**:
   - `tests/regression/test_desktop.py` expects `app.action_btn`, `app.canvas`, `app.indicator`, `app.status_label`, and specific button labels (`Start Recording`, `Copy to Clipboard`, `Audio to Ideas`).
   - All legacy attributes and methods must be strictly preserved.
4. **Documentation Integrity**:
   - All existing comments and docstrings in untouched areas remain preserved.
