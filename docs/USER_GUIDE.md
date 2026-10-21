# AI Voice Refiner — User Guide

**Target Audience:** End Users, Civil Engineers, Writers, Daily Loggers  
**Operating System:** Linux (Ubuntu 22.04 LTS – Ubuntu 26.04 LTS, Debian, Fedora, Arch)  
**Desktop Sessions:** Wayland & X11  

---

## 1. Quick-Start & Daily Shortcuts

You can control Voice-to-RefinedText from your terminal, desktop hotkey, or system tray.

### The 1-Letter Terminal Workflow (`v`)
Open your terminal in any directory and type:

```bash
v
```

```
╭──────────────── 🎙  VOICE DICTATION (Smart Bilingual) ────────────────╮
│ [● RECORDING]   Peak: 38%   Avg: 22%   [||||||||||············]        │
│ Speak naturally into your microphone... Press Ctrl+C to cancel.         │
╰─────────────────────────────────────────────────────────────────────────╯
```
- **Speaks $\rightarrow$ Transcribes $\rightarrow$ Refines $\rightarrow$ Copies to Clipboard**.
- Works in Bash, Zsh, and Tmux panes.

### Master Shell Shortcuts Reference

| Shortcut | Description | Example |
| :--- | :--- | :--- |
| **`v`** | Quick dictation with live animated Rich HUD | `v` |
| **`v -r`** | Dictation with **spoken audio readback** | `v -r` |
| **`v-doc`** | Runs 24-point self-healing system doctor | `v-doc` |
| **`v-speak "..."`** | Speaks text aloud using the Indian English neural voice | `v-speak "Report ready."` |
| **`v-read file.md`** | Reads an Obsidian Markdown file aloud | `v-read ~/daily/2026-10-21.md` |
| **`v-stop`** | Immediately interrupts speech playback | `v-stop` |
| **`Ctrl+G`** | In-prompt voice injection (types directly at your prompt) | Press `Ctrl+G`, speak `"git status"` |

---

## 2. Desktop Hotkey & Walkie-Talkie Mode

The background daemon (`tray_app.py`) listens globally for the hardware hotkey (default: **`Ctrl+Space`**):

1. **Walkie-Talkie (Push-to-Talk)**:
   - **Press and hold `Ctrl+Space`** while speaking.
   - **Release the keys**: The audio immediately processes, refines, and auto-pastes into your focused window (Obsidian, VS Code, Browser, LibreOffice).
2. **Hands-Free Toggle**:
   - **Tap `Ctrl+Space` briefly** (<300ms) to start hands-free recording.
   - **Tap `Ctrl+Space` again** when done speaking.
3. **Safe Clipboard Auto-Paste**:
   - The refiner copies the refined text, pastes it via your configured desktop tool (`wl-copy` on Wayland, `xclip`/`xdotool` on X11), and automatically restores your prior clipboard contents so you never lose copied code or URLs!

---

## 3. Web Settings Dashboard (`http://127.0.0.1:8765`)

Manage all system options in your browser without editing JSON files:

1. Right-click the system tray icon $\rightarrow$ **Settings**, or open your browser to:
   ```
   http://127.0.0.1:8765
   ```
2. **Dashboard Tabs**:
   - **Voice Refiner**: Switch ASR presets, base models folder, Whisper fallback, and Ollama models.
   - **Auto-Paste & Desktop**: Select paste behavior (`clipboard_restore`, `clipboard_only`, `direct_typing`) and tune typing delays.
   - **Evening Review**: Obsidian vault directories, question prompts, and TTS engines.
   - **Notifications**: Telegram bot notifications and morning briefing alarms.
   - **Doctor Diagnostics**: 1-click self-healing health check.

---

## 4. Evening Review & Obsidian Daily Notes

The interactive evening review (`review_engine.py`) conducts a structured, distraction-free voice debrief of your day:

1. **How to Trigger**:
   - Terminal: `python review_engine.py`
   - Web UI: Click **Start Review** on the dashboard.
   - Scheduled: Automatic reminder at 21:00.
2. **Structured Step-by-Step Prompts**:
   - **Step 1: Wellness & Energy**: Health, mood, personal reflection (saved to isolated private note).
   - **Step 2: Movement**: Physical activities or travel.
   - **Step 3: Meetings & Decisions**: Summarizes attendees, chairperson, and decisions into bullet points.
   - **Step 4: Daily Accomplishments**: Formats numbered paragraphs of wins.
   - **Step 5: Tomorrow's Priorities**: Builds a clean Markdown checkbox task list (`- [ ]`).
   - **Step 6: Core Focus Word**: Extracted single theme of the day.
3. **Automatic Task Carry-Forward**:
   - Incomplete tasks from the past 7 days are automatically extracted from your Obsidian notes and surfaced.
4. **Voice Narration**:
   - Each prompt is spoken aloud in your configured Indian voice.
   - Use `v-read` to hear your full daily note read back at any time.

---

## 5. PWD Uttarakhand Language & Terminology Helper

For civil engineers, tender officers, and bilingual government documentation:

1. **Acronym Lookup**:
   ```bash
   python pwd_cli.py EE
   # Output: [officers] EE = Executive Engineer (अधिशासी अभियंता)
   
   python pwd_cli.py NIT
   # Output: [works] NIT = Notice Inviting Tender (निविदा आमंत्रण सूचना)
   ```
2. **Keyword Search**:
   ```bash
   python pwd_cli.py search engineer
   # Output: Lists AE, EE, SE, CE, E-in-C with Hindi designations
   ```
3. **Sentence Translation**:
   ```bash
   python pwd_cli.py translate "Bridge inspection at Chamba is scheduled for tomorrow."
   # Output: Hindi translation with official PWD technical terms preserved
   ```

---

## 6. Self-Healing Diagnostics (`v-doc`)

If you ever experience issues with your microphone, GPU, or models, run:

```bash
v-doc
```

The unified doctor runs **24 diagnostic checks** across:
- Python environment & C-extensions (`transcribe_cpp`, `faster-whisper`, `numpy`)
- Model folder integrity (`/media/manoj/F1/models-handy`)
- Audio input/output hardware and PulseAudio/PipeWire status
- Wayland / X11 display server and evdev hardware permissions
- Ollama local LLM reachability and model availability
- Offers 1-click auto-healing for missing models or permissions.
