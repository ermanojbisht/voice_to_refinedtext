# 💡 AI Voice Refiner: The Vision

A **100% local, privacy-first, and professional-grade** voice-to-text assistant for Ubuntu. It transforms raw, garbled speech into polished, structured text using the power of **Whisper** and **Ollama**, without ever sending data to the cloud.

---

## ✅ Core Accomplishments (So Far)

*   **Offline Speech-to-Text**: High-speed transcription using `faster-whisper` (large-v3-turbo).
*   **Local AI Refinement**: Integration with `Ollama` for grammar cleanup and professional rewriting.
*   **Bilingual Intelligence**: Automatic detection and specialized handling for **English** and **Hindi**.
*   **Language-Specific Models**: Ability to use different LLMs for different languages (e.g., Qwen for English, Sarvam for Hindi).
*   **Interactive GUI**: A modern, dark-themed dashboard with pulsing recording animations and status tracking.
*   **Visual Settings**: A dedicated configuration window to manage models, hosts, and thresholds.
*   **System-Wide Trigger**: Global hotkey (`Ctrl+Alt+V`) for background execution.
*   **Auto-Clipboard**: One-click (or zero-click) integration with the system clipboard.
*   **Audio Feedback**: Professional sound cues for start, end, and completion.

---

## 🚀 The Path Ahead (New Ideas)

### 1️⃣ Modular "Engine" Refactor
*   Centralize logic into a single class to allow for multiple "front-ends" (Hotkey, Tray, Main GUI, CLI).

### 2️⃣ System Tray Presence (`pystray`)
*   A permanent resident in the Ubuntu top bar.
*   Shows recording status via icon color (Red/Blue/Green).
*   Quick-switch between "Refine" and "Translate" modes.

### 3️⃣ Auto-Translation Mode (Hindi 🎙️ ➔ English 📝)
*   Beyond just cleanup; a specialized mode to convert Hindi speech directly into professional English documentation.

### 4️⃣ Obsidian / Markdown Integration
*   Auto-save every transcription to a local Markdown vault with metadata (date, time, raw vs refined).

### 5️⃣ Direct Text Insertion
*   Instead of just copying to clipboard, the tool could simulate typing to insert text directly into the active window (Word, VS Code, Browser).

---

## 🧠 Architecture Evolution

```
[Trigger Layer: Hotkey / Tray / GUI]
            ↓
[Engine Layer: engine.py]
      /     |     \
 [Audio] [Whisper] [Ollama]
            ↓
[Provider Layer: Clipboard / Obsidian / Notifications]
```

---

## 🧩 Components Used
*   **STT**: `faster-whisper`
*   **LLM**: `Ollama` (Qwen 2.5/3.5, Sarvam-1)
*   **GUI**: `Tkinter / ttk`
*   **OS**: Ubuntu 20.04+ (X11/Wayland)
*   **Utils**: `sounddevice`, `xclip`, `xbindkeys`, `pystray`
