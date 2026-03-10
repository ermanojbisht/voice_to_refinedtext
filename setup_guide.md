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

## 2. Installation

### 2.1. Install System Packages
```bash
sudo apt update
sudo apt install python3-pip python3-venv python3-tk xclip xbindkeys pulseaudio-utils
```

### 2.2. Install Ollama & Models
Install Ollama via the official script:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Download the recommended models for high-quality English and Hindi refinement:
```bash
# Optimized English model (Fast)
ollama pull qwen3.5:0.8b

# High-quality Hindi model
ollama pull mashriram/sarvam-1:latest
```

### 2.3. Project Setup
Clone the project and set up the virtual environment:
```bash
cd /media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuration

### 3.1. Language-Specific Models
The system now supports different models for different languages. Configure them in `config.json`:
```json
{
    "OLLAMA_MODELS": {
        "en": "qwen3.5:0.8b",
        "hi": "mashriram/sarvam-1:latest"
    },
    "OLLAMA_HOST": "http://localhost:11434",
    "TEMPERATURE": 0.1
}
```

### 3.2. Prompt & Stop Customization
*   **Prompts**: Custom instructions for each model are stored in `prompts/{model_name}/{lang}.txt`.
*   **Stops**: To prevent models from "hallucinating" or continuing past the result, stop tokens are defined in `prompts/stops.json`.

## 4. Usage Modes

### Mode 1: Full GUI (Interactive)
Launch the main application window to see visual feedback, pulsing recording indicators, and an "Analyzing" progress bar.
```bash
python3 main_gui.py
```
*   **Start/Stop**: Control the recording manually or let silence detection handle it.
*   **Result**: View and edit the refined text before copying.
*   **Settings**: Quickly access configuration via the "Settings" button.

### Mode 2: Background Hotkey (Seamless)
Trigger the recording from anywhere in Ubuntu using a hotkey.

#### Setup with xbindkeys:
1. Create/Edit your configuration: `nano ~/.xbindkeysrc`
2. Add the following entry (adjust paths as needed):
   ```bash
   # AI Voice Refiner Hotkey
   "python3 /media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/voice_to_ai_clipboard.py"
     Control+Alt+v
   ```
3. Restart xbindkeys:
   ```bash
   killall xbindkeys && xbindkeys
   ```

## 5. Maintenance & Debugging

### 5.1. Configuration GUI
If you prefer not to edit JSON files manually, run the dedicated settings tool:
```bash
python3 config_gui.py
```
This allows you to select models from a list of what's currently installed in your Ollama.

### 5.2. Testing Models
Use the `compare_models.py` script to test how different models handle the same input text without recording audio:
```bash
python3 compare_models.py
```

### 5.3. Logs
All transcriptions and refinements are logged with timestamps in `log.json` for future reference.

## 6. Common Issues
*   **NameError/Undefined Variables**: Ensure you are using the latest version of `utils.py` and `voice_to_ai_clipboard.py`, as the model selection logic was recently updated to be dynamic.
*   **Ollama Timeout**: If the "Analyzing" phase takes too long, check if Ollama is under heavy load or if you need a smaller model (e.g., `qwen2.5-coder:1.5b`).
*   **No Result**: Check `prompts/stops.json`. If a model is not listed, it defaults to `\n` as a stop token, which can sometimes stop the response prematurely. Use `\n\n` for safer results.
