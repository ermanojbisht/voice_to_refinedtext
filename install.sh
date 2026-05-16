#!/bin/bash

# AI Voice Refiner - One-Click Installer for Ubuntu
# This script installs system dependencies, sets up the Python environment, 
# downloads AI models, and configures the global hotkey.

set -e # Exit on error

echo "🚀 Starting AI Voice Refiner Installation..."

# 1. Install System Dependencies
echo "📦 Installing system packages (sudo required)..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-tk xclip xbindkeys pulseaudio-utils curl \
    espeak-ng \
    python3-gi gir1.2-ayatanaappindicator3-0.1

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

# 5. Link System GObject (gi) to Venv
# This is required for pystray to use the AppIndicator backend on Ubuntu/GNOME
echo "🔗 Linking system GObject (gi) to virtual environment..."
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
ln -sf /usr/lib/python3/dist-packages/gi "$(pwd)/$VENV_DIR/lib/python$PYTHON_VERSION/site-packages/"

# 6. Make Scripts Executable
echo "🔐 Setting file permissions..."
chmod +x voice_to_ai_clipboard.py main_gui.py tray_app.py config_gui.py engine.py

# 7. Configure Global Hotkey (Ctrl+Alt+V)
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
echo "1. Run the Tray App: .venv/bin/python tray_app.py"
echo "2. Use the Hotkey: Ctrl+Alt+V (X11) or GNOME Custom Shortcut (Wayland)"
echo "3. Evening Review: right-click tray → Start Evening Review"
echo ""
echo "Wayland users: add a GNOME Custom Shortcut with command:"
echo "  pkill -USR1 -f tray_app.py"
echo ""
echo "Note: Ensure Ollama is running before starting the tray."
echo "===================================================="
