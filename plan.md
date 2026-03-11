# 🏗️ AI Voice Refiner: Development Plan

This plan outlines the phase-by-phase evolution of the project from a simple script into a fully integrated system-wide utility.

---

## Phase 1: Foundation (COMPLETED ✅)
*   **Core Logic**: Whisper transcription + Ollama refinement.
*   **Audio Handling**: Recording with silence detection.
*   **Bilingual Support**: Basic English/Hindi detection.
*   **Settings GUI**: First version of `config_gui.py`.
*   **Interactive GUI**: First version of `main_gui.py` with threading.
*   **Hotkey Setup**: Integration with `xbindkeys`.

---

## Phase 2: Refactoring & Robustness (CURRENT 🛠️)
*   **Modularization**: Create `engine.py` to decouple AI/Recording logic from UI code.
*   **Advanced Prompting**: Fine-tune `stops.json` and language-specific prompts.
*   **Dual-Model Support**: Support separate Ollama models for English and Hindi within the config and GUI.
*   **Stability**: Fix `NameError` and other runtime bugs.

---

## Phase 3: Visual Presence & Background Management
*   **Tray Icon Integration**: Use `pystray` for background management.
*   **Status Indicators**: Update tray icon color/shape based on the app state (Recording, AI processing).
*   **Main Window Polish**: Refine the GUI with better spacing, "Cancel" buttons, and more informative error messages.
*   **Settings Overhaul**: Extend `config_gui.py` to handle all new modular settings.

---

## Phase 4: Extended Modes & Features
*   **Auto-Translation Mode**: A new engine mode to translate Hindi 🎙️ ➔ English 📝.
*   **Transcription Templates**: Pre-configured prompts for different tasks (Meeting Notes, Professional Emails, Code Comments).
*   **Obsidian Integration**: Optional auto-save to a local Markdown vault.

---

## Phase 5: Ecosystem Integration
*   **Direct Text Insertion**: Explore using `xdotool` or `pynput` to paste text directly into the active application.
*   **VS Code Plugin (Experimental)**: A wrapper to trigger the refiner within the editor.
*   **Installer Script**: A single `install.sh` to handle all system dependencies and hotkey setups on a new machine.
