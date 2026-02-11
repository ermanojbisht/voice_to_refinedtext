# Voice-to-Refined Text AI Assistant Setup Guide

This guide provides instructions for setting up a fully local, offline-capable voice-to-text AI assistant on Ubuntu, which converts spoken language into refined text using Whisper and Ollama, and automatically copies it to the clipboard via a global hotkey.

## 1. System Requirements

*   **Operating System:** Ubuntu 20.04 (or newer compatible versions)
*   **Hardware:**
    *   Microphone for audio input.
    *   Sufficient CPU/GPU resources for running Whisper (STT) and Ollama (LLM). Model sizes can be adjusted based on available hardware.
*   **Software:**
    *   Python 3.8+
    *   `pip` (Python package installer)
    *   `git` (for cloning repositories)
    *   `xclip` (for clipboard integration)
    *   `ollama` (local LLM server)
    *   GNOME Desktop Environment (for hotkey configuration via `gsettings`)

## 2. Python Dependencies

The following Python packages are required. They will be installed into a virtual environment.

```
anyio==4.12.1
av==16.1.0
certifi==2026.1.4
cffi==2.0.0
charset-normalizer==3.4.4
click==8.3.1
ctranslate2==4.7.1
faster-whisper==1.2.1
filelock==3.20.3
flatbuffers==25.12.19
fsspec==2026.2.0
h11==0.16.0
hf-xet==1.2.0
httpcore==1.0.9
httpx==0.28.1
huggingface_hub==1.4.1
idna==3.11
langdetect==1.0.9
mpmath==1.3.0
numpy==2.4.2
onnxruntime==1.24.1
packaging==26.0
protobuf==6.33.5
pycparser==3.0
PyYAML==6.0.3
requests==2.32.5
scipy==1.17.0
setuptools==82.0.0
shellingham==1.5.4
six==1.17.0
sounddevice==0.5.5
sympy==1.14.0
tokenizers==0.22.2
tqdm==4.67.3
typer-slim==0.21.1
typing_extensions==4.15.0
urllib3==2.6.3
```

## 3. Setup Process

Follow these steps to set up the Voice-to-Refined Text AI Assistant on a new Ubuntu system.

### 3.1. Install System Dependencies

Open a terminal and run the following commands:

```bash
sudo apt update
sudo apt install python3-pip python3-venv git xclip
```

### 3.2. Install Ollama

If you don't have Ollama installed, follow the instructions on the [Ollama website](https://ollama.ai/download/linux) or use the following command:

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

After installation, ensure Ollama is running and download a model (e.g., `qwen2.5:3b`):

```bash
ollama pull qwen2.5:3b
```

### 3.3. Clone the Repository and Set Up Python Environment

Clone your project repository (assuming it's hosted on GitHub or similar):

```bash
git clone <your-repository-url> voice_to_refinedtext
cd voice_to_refinedtext
```

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

### 3.4. Configure the Python Script

Ensure your `voice_to_ai_clipboard.py` script is located in the `voice_to_refinedtext` directory. You might want to customize the `MODEL_SIZE` for Whisper or `OLLAMA_MODEL` within the script.

### 3.5. Configure Global Hotkey (GNOME)

This step needs to be done manually through the graphical user interface.

1.  **Open Settings:** Go to "Settings" -> "Keyboard" -> "Keyboard Shortcuts".
2.  **Add Custom Shortcut:** Scroll down to the bottom and click the "+" button to add a custom shortcut.
3.  **Fill in the details:**
    *   **Name:** `VoiceToAI`
    *   **Command:** `bash -c 'source /home/dell/Documents/voice_to_refinedtext/.venv/bin/activate && python3 /home/dell/Documents/voice_to_refinedtext/voice_to_ai_clipboard.py'`
        *   **Important:** Ensure the absolute path to your project directory (`/home/dell/Documents/voice_to_refinedtext/`) is correct in the command.
    *   **Shortcut:** Click on "Set Shortcut..." and press `Control+Alt+V` (or your desired key combination).
4.  **Click Add:** Close the settings.

### 3.6. Test the Hotkey

After configuring the hotkey, try pressing `Control+Alt+V`. Speak into your microphone for a few seconds. The processed text should be automatically copied to your clipboard. You can paste it into any application to verify.

## 4. Troubleshooting

*   **Hotkey not working:** Double-check the command and keybinding in GNOME settings. Ensure the paths are absolute and correct.
*   **Script errors:** Run the `voice_to_ai_clipboard.py` script directly from the terminal to see any error messages:
    ```bash
    cd /home/dell/Documents/voice_to_refinedtext
    source .venv/bin/activate
    python3 voice_to_ai_clipboard.py
    ```
*   **Ollama not running:** Ensure the Ollama server is running. You can check its status or restart it.
*   **Microphone issues:** Verify your microphone input settings in Ubuntu's sound settings.
