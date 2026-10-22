# Office Workstation Implementation & Setup Guide

**Target Audience:** Manoj Bisht / PWD Uttarakhand Office Workstation Setup  
**Operating System:** Linux (Ubuntu 22.04 LTS – Ubuntu 26.04 LTS, Debian, Linux Mint, Fedora)  
**Applicability:** Desktop PC, Work Laptop, or Intranet Workstation (100% Offline Capable)

---

## 1. Executive Summary & Architecture on Office Hardware

This system is engineered for **100% local, zero-cloud operation**. Once installed on your office workstation, it requires **zero external internet connectivity**—all speech recognition (Whisper / Nemotron / Apex), text refinement (Ollama Qwen / Llama-3 Hindi), and speech synthesis (Kokoro-82M ONNX) execute directly on your local CPU / Vulkan GPU with zero data leakage.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   OFFICE WORKSTATION RUNTIME                           │
│                                                                        │
│   [Hardware Microphone] ──> SoundDevice / PipeWire Ring Buffer         │
│                                      │                                 │
│   [Global Push-to-Talk] ──> Evdev Kernel Hotkey (Ctrl+Space)           │
│                                      │                                 │
│                                      ▼                                 │
│                     ┌────────────────────────────────┐                 │
│                     │  Local Speech Engine (CPU/GPU) │                 │
│                     │  • Instant English (Nemotron)  │                 │
│                     │  • Smart Bilingual (Whisper)   │                 │
│                     │  • Hinglish Notes (Apex)       │                 │
│                     └────────────────┬───────────────┘                 │
│                                      │                                 │
│                                      ▼                                 │
│                     ┌────────────────────────────────┐                 │
│                     │  Local Ollama LLM (Port 11434) │                 │
│                     │  • qwen2.5:3b (English PWD)    │                 │
│                     │  • llama3-hindi (Official Hindi)│                │
│                     └────────────────┬───────────────┘                 │
│                                      │                                 │
│                                      ▼                                 │
│   [Auto-Paste] ───────────> Focused App (LibreOffice, Browser, Mail)  │
│   [Speech Readback] ──────> Kokoro-82M ONNX Indian Voice               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: Pen Drive Checklist (What to Copy from Home PC)

Before leaving for the office, copy the following 3 folders onto a USB pen drive (or external SSD):

| Folder / Asset | Home PC Source Path | Purpose | Size |
| :--- | :--- | :--- | :--- |
| **1. Source Code Repository** | `/media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext` | Complete project files, scripts, and tests | ~50 MB |
| **2. ASR Speech Models** | `/media/manoj/F1/models-handy` | Whisper Turbo, Nemotron streaming, and Apex GGUF models | ~4.5 GB |
| **3. Kokoro TTS Neural Models** | `/media/manoj/F1/mkbmodel/kokoro-models` | `kokoro-v1.0.int8.onnx`, `kokoro-v1.0.onnx`, `voices-v1.0.bin` | ~450 MB |

> [!TIP]
> **Optional Ollama Models**: If your office PC has a restricted or air-gapped internet connection, you can also copy the Ollama models folder from your home PC (`~/.ollama/models`) to avoid re-downloading them over office Wi-Fi.

---

## 3. Phase 2: Office PC System Dependencies (APT)

Open a terminal on your office PC and run the following single command to install all audio, clipboard, and hotkey utilities:

```bash
sudo apt update && sudo apt install -y \
  python3-venv \
  python3-pip \
  sox \
  libasound2-dev \
  pulseaudio-utils \
  xclip \
  xdotool \
  wl-clipboard \
  ffmpeg
```

### Enable Global Push-to-Talk Without Root (`input` group)
To allow the Walkie-Talkie daemon (`Ctrl+Space`) to read hardware keypresses without needing `sudo`:

```bash
sudo usermod -aG input $USER
```

> [!IMPORTANT]
> You must **log out and log back in** (or restart) for the `input` group membership to take effect.

---

## 4. Phase 3: Project Setup & Virtual Environment

1. **Copy the repository to your office home directory**:
   ```bash
   cp -r /media/$USER/<YOUR_PENDRIVE>/voice_to_refinedtext ~/voice_to_refinedtext
   cd ~/voice_to_refinedtext
   ```

2. **Create and activate the virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -e ".[all]"
   ```

---

## 5. Phase 4: Place Offline Models & Configure Paths

1. **Create your office models directory**:
   ```bash
   mkdir -p ~/models/models-handy
   mkdir -p ~/models/kokoro-models
   ```

2. **Copy models from your pen drive**:
   ```bash
   # Copy ASR models
   cp -r /media/$USER/<YOUR_PENDRIVE>/models-handy/* ~/models/models-handy/

   # Copy Kokoro TTS models
   cp -r /media/$USER/<YOUR_PENDRIVE>/kokoro-models/* ~/models/kokoro-models/
   ```

3. **Update `config.json` with the office path**:
   Open `config.json` in your favorite editor (or modify it via the Web UI later):
   ```json
   {
       "MODELS_DIR": "/home/<your_username>/models/models-handy",
       "GLOBAL_HOTKEY": "Ctrl+Space"
   }
   ```
   *(Replace `<your_username>` with your office username, e.g. `/home/manoj/models/models-handy`)*.

---

## 6. Phase 5: Ollama Local LLM Setup on Office PC

1. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Pull the recommended office models**:
   ```bash
   # 1. Ultra-fast English civil engineering refiner (2.0 GB):
   ollama pull qwen2.5:3b

   # 2. Official Hindi government communication refiner:
   ollama pull SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest
   ```

   *(If your office PC has lower RAM, you can use `qwen2.5:1.5b` or `qwen2.5:3b` for both English and Hindi).*

---

## 7. Phase 6: Verification with Self-Healing Doctor (`v-doc`)

Run the automated diagnostic doctor to verify that all 6 subsystems are functioning properly on your office workstation:

```bash
python doctor.py
```

You should see:
```text
======================================================================
  🏥 UNIFIED VOICE-TO-REFINEDTEXT DIAGNOSTIC DOCTOR
  Platform: linux | Python: 3.xx | Status: PASS
======================================================================
▶ Python Environment: [PASS]
▶ Models & Portability: [PASS]
  [PASS] Kokoro TTS Models: Neural TTS ready
▶ Audio Hardware: [PASS]
▶ Desktop & Hotkeys: [PASS]
▶ Ollama LLM Service: [PASS]
▶ Batch & Media Tools: [PASS]
----------------------------------------------------------------------
  ✅ ALL SUBSYSTEMS HEALTHY — Application is ready for high-speed use!
----------------------------------------------------------------------
```

### Test Microphone Audio:
Run a live 1.5-second microphone signal probe:
```bash
python doctor.py --mic
```

---

## 8. Phase 7: Shell Integration & Desktop Autostart

### 1. Terminal Voice Command (`v`, `v-speak`, `v-read`)
Add the terminal voice helper to your office shell configuration:

```bash
echo "source ~/voice_to_refinedtext/scripts/terminal_voice.sh" >> ~/.bashrc
source ~/.bashrc
```

Now the `v` command is available anywhere in your terminal!

### 2. Desktop Autostart (Launch on System Boot)
To make the background Walkie-Talkie push-to-talk listener and system tray icon start automatically when you log into your office PC:

Create `~/.config/autostart/voice-refiner.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Voice Refiner Assistant
Exec=/bin/bash -c "cd $HOME/voice_to_refinedtext && source .venv/bin/activate && python tray_app.py"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Icon=audio-input-microphone
Comment=Universal Push-to-Talk Speech Refiner for Office
```

---

## 9. Phase 8: Daily Office Workflows

### Scenario 1: Walkie-Talkie Push-to-Talk Anywhere
1. Open your document in **LibreOffice Writer**, **Google Docs**, **MS Word Web**, **Email**, or **Obsidian**.
2. **Press and hold `Ctrl+Space`** on your keyboard.
3. Speak your note, e.g.:  
   *"The site inspection at Chamba division is completed. Foundation measurement book entries have been verified."*
4. **Release `Ctrl+Space`**.
5. Within 1 second, the speech is transcribed, refined according to official PWD standards, and **automatically pasted into your active document window**!

---

### Scenario 2: Quick Terminal Voice Dictation (`v`)
Whenever you are working in a terminal:
```bash
v
```
Speak your text, press `Enter` (or wait for silence), and the refined text is copied directly to your clipboard.

To dictate and have the system read it back to confirm accuracy:
```bash
v -r
```

---

### Scenario 3: PWD Acronym & Terminology Quick Lookup
Instant lookup of official Uttarakhand PWD designations and terms right from your prompt:

```bash
# Check officer designation
python pwd_cli.py EE
# -> [officers] EE = Executive Engineer (अधिशासी अभियंता)

# Check tender acronym
python pwd_cli.py NIT
# -> [works] NIT = Notice Inviting Tender (निविदा आमंत्रण सूचना)

# Translate phrase keeping official terms intact
python pwd_cli.py translate "Superintending Engineer has issued the administrative approval."
```

---

### Scenario 4: Natural Voice Narration (`v-speak` & `v-read`)
Have reports, logs, or notes read aloud in your preferred North Indian persona:

```bash
# 1. Read aloud using AIR Anchor baritone:
python pwd_cli.py --speak "Good morning Manoj. Reviewing third quarter milestone report." --tts-voice ni_air_anchor_m

# 2. Read an Obsidian daily note:
v-read ~/Documents/VoiceNotes/2026-10-22.md

# 3. Pipe terminal output into speech:
echo "Tender scrutiny complete. No defects found." | v-speak
```

---

### Scenario 5: Evening Daily Debrief (`review_engine.py`)
At the end of your workday (e.g. 5:30 PM), run:
```bash
python review_engine.py
```
The system will verbally prompt you through wellness, meetings, decisions, daily accomplishments, and tomorrow's priority checklist, automatically compiling your official daily journal entry into your Obsidian vault!

---

## 10. Office Troubleshooting Cheat Sheet

| Symptom | Probable Cause | Immediate Remediation |
| :--- | :--- | :--- |
| **`Permission denied: /dev/input/event*`** | User not in `input` group | Run `sudo usermod -aG input $USER` and log out/in. |
| **Microphone not detecting speech** | Wrong input device or muted | Run `python doctor.py --mic`. Open `pavucontrol` to verify the default input microphone level. |
| **`MODELS_DIR not found` in Doctor** | Path in `config.json` still points to home PC path (`/media/manoj/F1/...`) | Edit `config.json` to point to `~/models/models-handy` or `./models`. |
| **Auto-paste not typing into LibreOffice** | Display server is Wayland and `wl-clipboard` is missing | Install `wl-clipboard` (`sudo apt install wl-clipboard`). In settings, verify paste method is `clipboard_restore`. |
| **Ollama connection refused** | Ollama daemon not running | Run `ollama serve` or `sudo systemctl start ollama`. |
| **Speech playback silent** | PulseAudio / PipeWire audio player missing | Install `pulseaudio-utils` (`paplay`) or verify system sound output in Ubuntu Settings. |
