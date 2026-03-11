The local voice-to-text AI assistant setup is now complete and highly optimized.

**Summary of what has been done:**

1.  **Dependencies Installed:** `faster-whisper`, `sounddevice`, `scipy`, `requests`, `xclip`, and `langdetect` have been installed.
2.  **Advanced Python Script (`voice_to_ai_clipboard.py`):**
    *   **Auto-Stop Recording:** No longer fixed to 10 seconds. It automatically stops when it detects silence.
    *   **Language-Locked Prompts:** Uses `langdetect` to identify English vs. Hindi and applies specific AI prompts to prevent unwanted translation.
    *   **Sound Feedback:** Plays distinctive sounds for Start, End, and Completion of the process.
    *   **Ollama Integration:** Supports configurable host (local or server) and model settings via `config.json`.
3.  **Configuration Manager (`config_gui.py`):**
    *   A GUI tool to easily change Whisper models, Ollama host/model, silence sensitivity, and AI temperature.
4.  **Global Hotkey Setup:**
    *   `xbindkeys` is configured to trigger the assistant anywhere in Ubuntu using `Control+Alt+v`.

5. **Tray Icon Manager (`tray_app.py`):**
    *   A background resident that provides visual status (Recording/Processing) and manages the `Ctrl+Alt+V` hotkey.
    *   **Clickable Menu Fix**: Optimized for Ubuntu/Wayland by requiring `gir1.2-ayatanaappindicator3-0.1` and symlinking system `gi` to the virtual environment.
    *   **Robust Termination**: Uses signal handlers and `pynput.keyboard.Listener` for clean exit without errors.

**How to use the system:**

1.  **Run the Tray App (Recommended):** Use `.venv/bin/python tray_app.py`. This gives you a persistent icon and hotkey.
2.  **Adjust Settings (Optional):** Run `.venv/bin/python config_gui.py` to select your preferred models.
3.  **Ensure Ollama is running:** Make sure your Ollama server is active.
4.  **Press the Hotkey:** Press `Control+Alt+v` anywhere.
5.  **Speak:** You will hear a 'start' sound. The script will automatically stop after a few seconds of silence.
6.  **Paste:** The refined text is automatically copied to your clipboard.

**Troubleshooting Tray Icons:**
If the icon is visible but the menu doesn't open on click, ensure you have run the installer or manually installed `gir1.2-ayatanaappindicator3-0.1` and created the `gi` symlink in your `.venv`.

**File Locations:**
- Main Script: `/media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/voice_to_ai_clipboard.py`
- Settings GUI: `/media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/config_gui.py`
- Logs: `/media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/log.json`

**Note:** If the AI is still hallucinating or translating unexpectedly, you can adjust the "AI Temperature" in the Settings GUI to a lower value (e.g., 0.1).