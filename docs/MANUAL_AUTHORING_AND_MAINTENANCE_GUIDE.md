# AI Agent SOP: Manual Authoring, Maintenance & Auto-Sync Guide

## 1. Executive Summary & Philosophy

In this codebase, **documentation is an executable system asset, not a secondary byproduct**. 

The master user manual lives in `docs/CONFIGURATION_GUIDE.md`. The GUI Help & Manual viewer (`manual_gui.py`), System Tray app (`tray_app.py`), and Settings GUI (`config_gui.py`) automatically parse and present this document directly to the end user as structured interactive cards and HTML.

> [!IMPORTANT]
> **Single Source of Truth Rule**:
> NEVER hardcode manual text, instructions, or configuration guides inside GUI Python widgets (`main_gui.py`, `config_gui.py`, `tray_app.py`). All user-facing documentation must be authored in `docs/CONFIGURATION_GUIDE.md`. The system dynamically parses and renders it. When the Markdown file is updated, the GUI manual updates instantly with zero dual effort.

---

## 2. Document Hierarchy & Structure for Automated Parsers

The dynamic manual engine (`manual_service.py`) relies on standard Markdown syntax to split documents into navigable chapters, sidebar parts, searchable index tokens, and formatted visual cards.

### 2.1 Heading Hierarchy (Required for Chapter Splitting)

The parser splits chapters using top-level `## N. <Chapter Title>` headings:

```markdown
## 1. Quick-Start Hardware Presets
### 1.1 Preset A: High-Performance GPU Workstation
### 1.2 Preset B: Low-VRAM / Office Desktop

## 2. Core Voice Refiner (`config.json`) Reference
### 2.1 Engine Settings
### 2.2 Features & Toggles

## 9. Best Practice Matrix: Speed + Accuracy for Input Audio vs Output Goal
### 9.1 Speed + Accuracy Decision Matrix
### 9.2 Key Architectural Principles
```

- **Level 1 (`# ...`)**: Document Title only (only one allowed at the top of the file).
- **Level 2 (`## N. ...`)**: Creates a distinct **Chapter / Part** in the GUI sidebar and HTML table of contents. Always prefix with a number (`## 1.`, `## 2.`, etc.).
- **Level 3 (`### N.M ...`)**: Creates collapsible sections or card headers within the chapter.
- **Level 4 (`#### ...`)**: Minor sub-headings or parameter groupings.

---

### 2.2 Standard Configuration Table Schema

Whenever you add or modify a configuration setting, you **must** use the standardized 5-column Markdown table. The parser uses these exact headers to generate interactive settings tables:

```markdown
| Configuration Key | Type | Default | Valid Options | Description & Performance Impact |
|---|---|---|---|---|
| `SAMPLE_RATE` | `integer` | `16000` | `16000`, `44100`, `48000` | Audio sampling frequency in Hz. Required 16000 for Whisper/Nemotron. |
| `LANGUAGE_MODE` | `string` | `"bilingual"` | `"bilingual"`, `"pure_english"`, `"pure_hindi"`, `"roman_hinglish"` | Language refinement strategy for Ollama and ASR coupling. |
| `OLLAMA_KEEP_ALIVE` | `string` | `"60m"` | `"0"`, `"5m"`, `"60m"`, `"-1"` | GPU VRAM retention duration. Set `"0"` for low VRAM to free GPU memory immediately. |
```

---

### 2.3 Standard Best Practice & Decision Matrix Schema

When documenting model selections, hardware combinations, or performance profiles, use the 8-column matrix:

```markdown
| Input Speech Type | Target Output Goal | Optimal ASR Profile | Language Mode (`LANGUAGE_MODE`) | Recommended LLM (`OLLAMA_MODELS`) | End-to-End Latency | Accuracy Rating | Why This Combination Excels |
|---|---|---|---|---|---|---|---|
| **Pure English** | **Official English** | `nemotron_fast` | `pure_english` | `qwen2.5:3b` | **~0.8s** | **100%** | English-only tokens prevent Devanagari confusion. |
```

---

### 2.4 Callouts & Visual Badges

Use GitHub-style alert callouts. The HTML converter automatically renders these with themed Catppuccin color accents, glowing borders, and icons:

```markdown
> [!NOTE]
> Background information, configuration context, or general explanations.

> [!TIP]
> Optimization tricks, speed enhancements, or latency reduction recommendations.

> [!IMPORTANT]
> Critical configuration parameters, required dependencies, or mandatory rules.

> [!WARNING]
> High-risk settings, VRAM exhaustion risks, or breaking behavior changes.
```

---

### 2.5 Code Blocks & Hardware Presets

- Always include the language tag (e.g., ````json````, ````bash````, ````python````).
- Configuration JSON snippets must be 100% valid JSON, copy-paste ready directly into `config.json`.
- Terminal commands must use copy-ready shell syntax with comments.

---

### 2.6 Screenshots & Visual Assets

- Place all screenshots, SVG icons, and architectural flowcharts in `docs/assets/`.
- Reference them using relative Markdown image paths: `![Tray Status Icon](assets/tray_idle.png)`.
- The HTML converter automatically resolves `assets/` relative to the document directory.

---

## 3. AI Agent Step-by-Step Update Protocol (SOP)

Whenever an AI agent is assigned a coding task that alters functionality, the agent must follow this 4-step protocol before completing the turn:

```
[Step 1: Code Implementation]
       │
       ▼
[Step 2: Impact Analysis] ──► Identify affected manual chapters (Presets, Settings, Matrix, CLI)
       │
       ▼
[Step 3: Update `docs/CONFIGURATION_GUIDE.md`] ──► Follow schemas (Tables, Callouts, Headings)
       │
       ▼
[Step 4: Verify via `manual_service.py`] ──► Confirm clean parse without syntax errors
```

### Protocol Checklist:

1. **If adding a new configuration key**:
   - [ ] Add the key to `utils.py` (`load_config` defaults).
   - [ ] Add the row to `docs/CONFIGURATION_GUIDE.md` Section 2 (or Section 3 for review, Section 4 for audio-to-idea).
   - [ ] Check if Hardware Presets (Section 1) need updating to reflect the new feature.

2. **If adding an ASR engine or profile**:
   - [ ] Define the profile in `audio_to_idea/asr/` and `config.json` (`MODEL_PROFILES`).
   - [ ] Add the profile to the Speed + Accuracy Matrix in Section 9 of the guide.
   - [ ] Document memory requirements, latency, and supported languages.

3. **If changing a prompt mode or language option**:
   - [ ] Create/update prompt files in `prompts/default/` and model-specific folders (`prompts/qwen2.5_3b/`, `prompts/llama3_hindi/`).
   - [ ] Update Section 9 with the exact combination recommendation.

4. **If modifying terminal CLI commands or GUI shortcuts**:
   - [ ] Update Section 5 (`pwd_cli.py` reference) or Section 7 (Settings adjustments).

---

## 4. How the Manual System Operates in Code

```
docs/CONFIGURATION_GUIDE.md (Markdown source)
         │
         ▼
manual_service.py (Auto-parser & HTML Renderer)
         ├── get_chapters()  ──► Parses ## N. headings into navigable JSON tree
         ├── get_chapter(n)  ──► Returns single chapter content + parsed tables
         └── export_html()   ──► Compiles full styled HTML page with Catppuccin theme
         │
         ├──► manual_gui.py  (Interactive CustomTkinter Window with Sidebar + Search)
         ├──► tray_app.py    (Right-click menu: "📖 User Manual & Help")
         └──► config_gui.py  (Header button: "📖 Help & Manual")
```

- **MTime Caching**: `manual_service.py` tracks the modification time (`os.path.getmtime`) of `docs/CONFIGURATION_GUIDE.md`. If the file hasn't changed, cached chapter objects are served in <1ms.
- **Zero Build Step**: No compilation or external web server is needed. The Python `markdown` library converts directly to HTML, opened via `webbrowser.open()` or viewed in the native GUI.

---

## 5. Verification Commands for AI Agents

To verify that the manual is healthy and all chapters are cleanly recognized:

```bash
# Run manual service verification
python3 -c "import manual_service; print(manual_service.get_chapter_summary())"

# Export and check HTML generation
python3 -c "import manual_service; print(manual_service.generate_html_manual())"
```

Keep this standard in mind for all ongoing and future development tasks.
