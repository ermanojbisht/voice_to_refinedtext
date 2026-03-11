# Voice-to-Refined Text AI Assistant Setup Guide

This guide provides detailed instructions for setting up a fully local, offline-capable voice-to-text AI assistant on Ubuntu. The system converts spoken language (English or Hindi) into refined, professional text using Whisper and Ollama, then automatically copies it to the clipboard.

## 1. System Requirements

*   **Operating System:** Ubuntu 20.04 (or newer)
*   **Hardware:**
    *   Microphone for audio input.
    *   8GB+ RAM recommended (depending on the Ollama models used).
*   **System Dependencies:**
    *   `python3`, `pip`, `python3-tk` (for GUIs)
    *   `xclip` (for clipboard management)
    *   `xbindkeys` (for reliable global hotkeys)
    *   `pulseaudio-utils` (for `paplay` sound feedback)
    *   `ollama` (the local AI engine)
    *   `python3-gi`, `gir1.2-ayatanaappindicator3-0.1` (Required for clickable tray icons on Ubuntu/GNOME)

## 2. Installation (Automatic)

The easiest way to set up the system is using the provided `install.sh` script. This script handles system packages, Ollama, AI models, and hotkey configuration in one go.

```bash
cd voice_to_refinedtext
chmod +x install.sh
./install.sh
```

## 3. New PC Deployment Guide (Detailed)

If you are setting up this project on a brand-new machine, follow this detailed breakdown to ensure everything works perfectly.

### 3.1. What `install.sh` Actually Does
The installer is more than just a script; it's a bridge between the AI and your Linux desktop:
*   **System Dependencies**: Installs `xclip` (clipboard), `xbindkeys` (hotkeys), and `pulseaudio-utils` (sound).
*   **Tray Icon Logic**: Installs `python3-gi` and `gir1.2-ayatanaappindicator3-0.1` so the tray icon becomes clickable on Ubuntu/GNOME.
*   **AI Infrastructure**: Automatically installs **Ollama** and pre-pulls the required models (`qwen3.5`, `qwen2.5`, and `sarvam-1`) so you don't have to wait later.
*   **Python Isolation**: Creates a `.venv` and performs a **System-to-Venv Symlink** for `gi`. This is a critical step because standard `pip` cannot install the Linux-native libraries needed for the tray icon.
*   **Global Hotkey**: Configures `~/.xbindkeysrc` so that `Ctrl+Alt+V` works system-wide immediately.

### 3.2. Step-by-Step Setup on a New PC
1.  **Clone/Copy the Project**: Place the `voice_to_refinedtext` folder in your preferred directory.
2.  **Run the Installer**:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```
    *Note: Provide your sudo password when prompted for system packages.*
3.  **Start the Tray Manager**:
    ```bash
    .venv/bin/python tray_app.py
    ```
4.  **Test the Hotkey**: Press `Ctrl+Alt+V`. You should hear a start sound and see the tray icon turn red.
5.  **Optional: Auto-Start on Boot**:
    *   Open "Startup Applications" in Ubuntu.
    *   Click "Add".
    *   **Command**: `/path/to/project/.venv/bin/python /path/to/project/tray_app.py` (Use absolute paths).

## 4. Manual Configuration (Advanced)

### 4.1. Language-Specific Models
The system now supports different models for different languages. Configure them in `config.json`:
```json
{
    "OLLAMA_MODELS": {
        "en": "qwen2.5:3b",
        "hi": "mashriram/sarvam-1:latest"
    },
    "OLLAMA_HOST": "http://localhost:11434",
    "TEMPERATURE": 0.1
}
```

### 4.2. Prompt & Stop Customization
*   **Prompts**: Custom instructions for each model are stored in `prompts/{model_name}/{lang}.txt`.
*   **Stops**: To prevent models from "hallucinating" or continuing past the result, stop tokens are defined in `prompts/stops.json`.

## 5. Usage Modes

### Mode 1: Tray App (Recommended for Background Use)
The tray app sits in your top bar, provides visual status via icon color, and handles the global hotkey.
```bash
.venv/bin/python tray_app.py
```
*   **Gray Icon**: Idle.
*   **Red Icon**: Recording.
*   **Blue Icon**: Processing.
*   **Wayland Note**: On Ubuntu Wayland (GNOME), the tray menu requires `AppIndicator` support. The installer automatically handles the system symlinks to enable this.

### Mode 2: Full GUI (Interactive)
Launch the main application window to see visual feedback, pulsing recording indicators, and an "Analyzing" progress bar.
```bash
.venv/bin/python main_gui.py
```
*   **Start/Stop**: Control the recording manually or let silence detection handle it.
*   **Result**: View and edit the refined text before copying.
*   **Settings**: Quickly access configuration via the "Settings" button.

### Mode 3: Background Hotkey (Seamless)
Trigger the recording from anywhere in Ubuntu using a hotkey.

#### Setup with xbindkeys:
1. Create/Edit your configuration: `nano ~/.xbindkeysrc`
2. Add the following entry (adjust paths as needed):
   ```bash
   # AI Voice Refiner Hotkey
   "/absolute/path/to/project/.venv/bin/python /absolute/path/to/project/voice_to_ai_clipboard.py"
     Control+Alt+v
   ```
3. Restart xbindkeys:
   ```bash
   killall xbindkeys && xbindkeys
   ```

## 6. Maintenance & Debugging

### 6.1. Configuration GUI
If you prefer not to edit JSON files manually, run the dedicated settings tool:
```bash
.venv/bin/python config_gui.py
```
This allows you to select models from a list of what's currently installed in your Ollama.

### 6.2. Testing Models
Use the `compare_models.py` script to test how different models handle the same input text without recording audio:
```bash
.venv/bin/python compare_models.py
```

### 6.3. Logs
All transcriptions and refinements are logged with timestamps in `log.json` for future reference.

## 7. Common Issues
*   **Tray Icon Not Clickable**: Ensure `gir1.2-ayatanaappindicator3-0.1` is installed (`sudo apt install gir1.2-ayatanaappindicator3-0.1`) and that the `gi` package is symlinked to your `.venv/lib/python3.x/site-packages/` directory.
*   **Tray App Termination Error**: If the tray app shows errors on exit, ensure you are using the latest version with the improved signal handling logic.
*   **NameError/Undefined Variables**: Ensure you are using the latest version of `utils.py` and `voice_to_ai_clipboard.py`, as the model selection logic was recently updated to be dynamic.
*   **Ollama Timeout**: If the "Analyzing" phase takes too long, check if Ollama is under heavy load or if you need a smaller model (e.g., `qwen2.5-coder:1.5b`).
*   **No Result**: Check `prompts/stops.json`. If a model is not listed, it defaults to `\n` as a stop token, which can sometimes stop the response prematurely. Use `\n\n` for safer results.
