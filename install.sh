#!/bin/bash

# AI Voice Refiner - One-Click Installer for Ubuntu
# This script installs system dependencies, sets up the Python environment, 
# downloads AI models, and configures the global hotkey.

set -e # Exit on error

echo "🚀 Starting AI Voice Refiner Installation..."

# 1. Install System Dependencies
echo "📦 Installing system packages (sudo required)..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-tk xclip xbindkeys pulseaudio-utils curl

# 2. Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "🦙 Ollama not found. Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama is already installed."
fi

# 3. Download Recommended Models
echo "🧠 Pulling AI models from Ollama (this may take a few minutes)..."
ollama pull qwen3.5:0.8b
ollama pull qwen2.5:3b
ollama pull mashriram/sarvam-1:latest

# 4. Set up Python Virtual Environment
echo "🐍 Setting up Python virtual environment..."
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Make Scripts Executable
echo "🔐 Setting file permissions..."
chmod +x voice_to_ai_clipboard.py main_gui.py tray_app.py config_gui.py engine.py

# 6. Configure Global Hotkey (Ctrl+Alt+V)
echo "⌨️ Configuring global hotkey..."
XBINDKEYS_CONFIG="$HOME/.xbindkeysrc"
SCRIPT_PATH="$(pwd)/voice_to_ai_clipboard.py"
VENV_PYTHON="$(pwd)/$VENV_DIR/bin/python3"

# Check if the hotkey is already in the file
if [ -f "$XBINDKEYS_CONFIG" ] && grep -q "$SCRIPT_PATH" "$XBINDKEYS_CONFIG"; then
    echo "✅ Hotkey already configured in $XBINDKEYS_CONFIG"
else
    echo "Adding hotkey to $XBINDKEYS_CONFIG..."
    cat <<EOT >> "$XBINDKEYS_CONFIG"

# AI Voice Refiner Hotkey
"$VENV_PYTHON $SCRIPT_PATH"
  Control+Alt+v
EOT
fi

# Restart xbindkeys to apply changes
killall xbindkeys || true
xbindkeys

echo ""
echo "===================================================="
echo "🎉 INSTALLATION COMPLETE!"
echo "===================================================="
echo "1. Run the Tray App: python3 tray_app.py"
echo "2. Run the Dashboard: python3 main_gui.py"
echo "3. Use the Hotkey: Press Ctrl+Alt+V from anywhere"
echo ""
echo "Note: Ensure Ollama is running in the background."
echo "===================================================="
