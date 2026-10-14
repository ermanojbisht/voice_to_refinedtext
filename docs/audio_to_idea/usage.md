# Audio to Ideas — user guide

AudioToIdea processes saved recordings locally. It has a CLI and a dedicated desktop window; the existing recorder, clipboard workflow and Evening Review continue to use their own settings and outputs. For development and maintenance, see the [developer guide](developer_guide.md).

## Start on this PC

```bash
python3 -m audio_to_idea gui
python3 -m audio_to_idea doctor --discover --check-ollama
python3 -m audio_to_idea transcribe --input /path/to/note.m4a
python3 -m audio_to_idea process --input /path/to/recordings --context "Road inspection review"
```

Use **Audio to Ideas** in the tray or main window when integration is enabled in the module settings. Existing tray/window processes see launch-entry changes after their next normal restart. Direct CLI/GUI launch always works regardless of the visibility setting.

**Add files** or **Add folder**, optionally select a context profile or type background, choose a mode, then **Transcribe + process**. **Transcript only** skips Ollama. Click a queue entry to view its transcript and processed text. Essential settings have explanations beneath them and supplemental hover tooltips. **Check setup** inspects assets without loading a large model.

## Processing modes and editable prompts

**1. Clean paragraph** is the default for new and existing settings files without an explicit mode. It improves grammar, punctuation and flow while preserving meaning. **2. Concise summary** produces a shorter factual restatement. **3. Ideas and actions** retains the structured operational extraction workflow. These mode changes apply to AudioToIdea; the existing Voice Refiner/Review prompt files and defaults are unchanged.

| Mode setting / CLI value | Result beside a recording named `note.wav` |
|---|---|
| `clean_paragraph` | `note_clean.txt` |
| `concise_summary` | `note_summary.txt` |
| `ideas_actions` | `note_idea.txt` |

The transcript remains `note.txt` (plus any selected subtitle/JSON formats). Mode outputs coexist. The GUI **Processed text** panel shows the latest completed result; changing the mode does not rewrite that result until **Regenerate selected** is run.

Default output language is **source**: English stays English, Hindi stays Devanagari, and Hindi-English speech keeps its natural mix and English technical terms. Select **English** or **Hindi** explicitly to translate. Paragraph/summary processing checks scripts, numeric figures, dates, technical acronyms and negative statements; one correction is attempted when a check fails. A persistent failure preserves transcription and reports a partial result. These are targeted checks, not a guarantee that every semantic detail is correct. Review the processed text against the recording/transcript.

Click **Edit prompt** to edit the selected mode's template. **Preview** substitutes the selected transcript (up to 5,000 characters), background and output-language policy without invoking Ollama. Runtime JSON/language/figure rules are enforced separately. **Restore built-in text** fills the editor with the packaged template; click **Save custom prompt** to apply it. Unsaved edits are checked on close.

Saving creates a personal mode file under the chosen folder; the default is `audio_to_idea_prompts/` beside your module settings. It does not alter legacy or packaged prompts. Each mode uses its own filename (`clean_paragraph.txt`, `concise_summary.txt`, `ideas_actions.txt`). The selected folder is saved in `synthesis.prompt_directory`. Missing mode files use their packaged defaults.

Available placeholders:

- `{transcript}` — required exactly once; the app supplies the transcript section.
- `{context}` — optional project background, not spoken evidence.
- `{output_language}` — optional requested language or explicit source-preservation policy.

JSON examples with literal braces can be included. Unknown named placeholders, invalid UTF-8, empty files and prompts larger than 64 KiB are rejected. The model response schema stays fixed for the selected mode. A custom instruction can change style or domain focus but must retain that response contract.

For CLI-specific customization, `--prompt-file` overrides the selected mode's template; it does not save settings. `synthesis.prompt_file` provides a persistent single-file override. Switching modes through the GUI clears that override and uses each mode's saved folder template. Active batches/watch sessions freeze their prompt bytes; edits apply to the next run/session. Prompt content is hashed, so editing a file invalidates processed-output reuse even when its path stays the same. Matching ASR is reused.

Long recordings are processed in bounded transcript sections and their paragraphs/summaries are joined in source order. Summary mode produces section summaries for input larger than the context budget rather than silently truncating the recording.

## Window appearance and layout

Choose **Light**, **Dark** or **System** in the window header. Your choice is saved as `ui.appearance` in the module settings; existing files without this field default to System. System follows the theme reported to CustomTkinter by the desktop. Some Linux desktops do not report it, so use Light or Dark explicitly there.

The window uses blue–green gradients, frosted panel fills and soft rounded edges. Enabled primary buttons have white labels on blue; disabled actions use a readable muted fill. Dropdown arrows and menus have explicit theme-aware colours. The glass appearance is drawn inside Tk (frosted gradients, without native desktop blur). Gradient painting responds to resizing and appearance changes.

The recording sidebar, transcript editor and ideas panel resize with the window. **Add background** expands the optional profile path and project notes; **Hide background** frees space without discarding those notes. Settings are grouped into **Models**, **Audio**, **Output** and **Preferences** tabs. Cached-model discovery runs in the background so a slow disk does not freeze the window.

The footer shows the processing stage and a progress indicator. Chunk progress describes transcription, not the remaining duration of the entire job. **Stop** requests a safe cancellation; it may wait for the current inference call. Processing and revision buttons reflect the current selection and job state. Clicking the selected recording again preserves unsaved edits.

## Settings and another PC

The module uses `audio_to_idea_config.json` beside this repository's main config. Installed standalone packages use a settings file in the current working directory. `--config /path/to/settings.json` or `AUDIO2IDEA_CONFIG` selects another file. Copy `audio_to_idea_config.example.json`, then change model/cache paths for the destination computer.

This PC's machine-local file selects the existing cache under `/media/manoj/F1/huggingface_cache/hub` and converted large-v3 weights. That path is not compiled into the program or shipped as a portable default. **Settings → Discover models** lists complete snapshots and explains incompatible/broken ones. Select either a compatible repository/cache/revision or a complete model folder. At equal precedence a model folder takes priority over repository lookup; a higher-priority CLI/environment model, revision, or cache selection overrides a lower-priority saved folder.

`openai/whisper-large-v3` contains Transformers weights, not the converted weights needed by faster-whisper. Choose `Systran/faster-whisper-large-v3` or a compatible turbo snapshot. The currently broken OpenAI `main` snapshot is reported rather than repaired or silently substituted. Missing model cache on another PC gives setup guidance; no download occurs by default.

Relative file-config paths are resolved beside that file; relative CLI/environment paths use the invocation directory. `~` and `$VARIABLE`/`${VARIABLE}` expansion work, with an error for unset variables. CLI overrides never save configuration; the GUI saves only edited fields in its separate module settings file. A theme change saves only `ui.appearance`. Existing relative paths and unknown extension keys are retained, and unchanged environment overrides are not copied into the settings file.

Effective precedence is CLI → environment → module settings → the limited read-only legacy fallback → defaults. Legacy fallback may supply `WHISPER_MODEL`, `OLLAMA_HOST`, and `OLLAMA_MODELS.en`. It does not import microphone silence settings or existing Markdown destinations.

Environment overrides:

| Variable | Field |
|---|---|
| `AUDIO2IDEA_CONFIG` | Settings file |
| `AUDIO2IDEA_MODEL_PATH` / `ASR_MODEL_PATH` | Complete converted model directory; conflicting aliases are rejected |
| `AUDIO2IDEA_MODEL_ID` | Cached repository/model alias |
| `AUDIO2IDEA_CACHE_ROOT` | Hugging Face hub cache root |
| `AUDIO2IDEA_REVISION` | Selected snapshot |
| `AUDIO2IDEA_DEVICE` / `AUDIO2IDEA_COMPUTE_TYPE` | Hardware/precision |
| `AUDIO2IDEA_OLLAMA_HOST` / `AUDIO2IDEA_OLLAMA_MODEL` | Text processing service/model |
| `AUDIO2IDEA_MODE` | Processing mode |
| `AUDIO2IDEA_PROMPT_FILE` | Selected mode's custom template |

Standard `HF_HUB_CACHE`, `HUGGINGFACE_HUB_CACHE`, and `HF_HOME` apply when no module cache root is set. `doctor` reports effective settings and their source. Use **Offline mode** for cached models and localhost Ollama. Cloud-tagged Ollama models and remote endpoints are rejected in offline mode. Discovery/doctor never downloads, even if downloads are allowed for processing.

For CPU operation, select `device: "cpu"` and `compute_type: "auto"`; smaller compatible cached models reduce processing time. `auto` attempts available CUDA and falls back to CPU if model loading fails. Explicit CUDA fails clearly instead of silently changing device. Apple MPS and raw Transformers backends are not included in this release.

## CLI controls

```bash
# Several output formats; original audio is unchanged
python3 -m audio_to_idea transcribe -i note.mp3 -o ./outputs -f txt -f srt -f json

# Choose paths/hardware on another computer
python3 -m audio_to_idea transcribe -i note.wav --cache-root /path/to/hub --model-id tiny --device cpu

# Supply a project glossary/background profile; use a separate idea model
python3 -m audio_to_idea process -i ./recordings --mode ideas_actions --profile ./project_context.json --synthesis-model qwen2.5:3b

# Clean paragraph is the default; preserve the original language mix
python3 -m audio_to_idea process -i note.wav

# Short summary with a tailored template, optionally translated to English
python3 -m audio_to_idea process -i note.wav --mode concise_summary --prompt-file my_summary.txt --output-language English

# Watch completed copies; Ctrl+C stops safely
python3 -m audio_to_idea watch -i ./incoming -o ./outputs --stable-seconds 5 --recursive
```

`transcribe` never invokes Ollama. `process --no-summary` is also transcript-only in every mode. `--context-file` and inline `--context` supplement a selected profile. `--model` selects ASR; `--synthesis-model` selects Ollama. Repeat `--format` for TXT/SRT/VTT/JSON. Use `--chunk-size`, `--overlap`, `--language`, `--revision`, and `--overwrite` when needed; `--help` lists exact options.

CLI exit codes: 0 success, 2 invalid configuration/setup/command input, 3 failed or partially successful batch, 130 cancellation. `--json` produces a results object on stdout with progress on stderr. Watch mode reports progress/results on stderr until interrupted.

## Outputs, recovery and corrections

Human-facing outputs retain the recording stem: `.txt`/`.srt`/`.vtt`/`.json`, the selected `_clean.txt`/`_summary.txt`/`_idea.txt`, and optional `.meta.json`. Metadata records the processing mode, model and prompt hash. Directory batches preserve subfolders; identical stems across extensions receive a deterministic extension suffix, with an additional hash for case collisions. Hour-safe timestamps refer to original recording time. Optional normalization never deletes silence or overwrites the source.

A hidden `.audio2idea` directory under the output folder holds manifests, chunk checkpoints, raw transcripts, edited revisions and cached processed text/ideas. Retain it for resume and reuse. Rerun the same command to resume compatible work; completed ASR is reused when only background, mode, prompt or synthesis settings change. Changing a profile's **glossary** can rerun ASR because the glossary guides Whisper's recognition. A synthesis failure leaves transcript outputs intact. `--overwrite` forces processing but does not authorize destruction of unrelated or manually edited output files; choose another output folder for those cases.

In the GUI's **Editable** transcript panel, keep segment IDs such as `[S00001]`, correct the words, then **Save transcript revision** after processing finishes. The **Raw ASR** panel stays unchanged. **Regenerate selected** retries unfinished work or regenerates exports and the selected mode's output using the corrected revision without repeating valid ASR. Ideas mode uses readable headings and bullets, cites evidence segment IDs/timestamps, and explicitly labels inferred suggestions. Plain paragraph/summary files and idea reports remain available in the output folder. Verify technical terms, figures and claims against the original audio before relying on them.

Ideas should be proportional to the recording. Greetings, microphone tests and requests to copy/transcribe speech do not constitute a project review, even when a project profile is selected. With no substantive findings, the result is simply **No actionable ideas identified in this recording.** Only populated categories appear in the human-readable report; the internal structured JSON retains all three categories for CLI/GUI compatibility. In source-language mode, items labeled as spoken must quote their cited transcript. For another output language, translated text includes an original-language source quote in structured JSON for validation. Repeated findings across categories are rejected rather than displayed as independent evidence. One bounded correction attempt is allowed; failure still preserves the transcript. These checks reduce false output but do not replace reviewing inferred suggestions for relevance.

Prompt updates invalidate only cached processed text/ideas. Rerun processing or regenerate the selected recording to apply the current template. Restart a window that was opened before a software update to load the new code; matching transcription is reused. Source audio and transcript revisions are preserved.

Cancellation occurs at safe checkpoints; an in-progress ASR segment or a slow Ollama packet may delay stopping. Closing the window waits for that safe stop. Completed stages remain available. Watch mode waits for size/mtime stability and a decodable source, retries failed files at most three times with backoff, then pauses them until a change or watcher restart. Generated outputs/workspaces are excluded.

## Coexistence with the old app

The old recorder announces microphone activity without waiting for batch inference. Its transcription and Ollama calls share a process lock with AudioToIdea. A pending old-app inference request gets priority before the next batch chunk; currently executing inference is not preempted. AudioToIdea releases its own Whisper weights before synthesis by default. It never forcibly unloads another process's resident model. If VRAM is insufficient, select CPU or retry after other GPU work finishes. Existing wake-word control already uses its own small CPU model and remains independent.

The optional setting `integration.enabled` controls new launch entries. Disabling it restores the old menu/window layout on next startup; direct AudioToIdea commands still work. No vault paths, note templates, hotkeys, timers or notification configuration are migrated.

## Installation and verification

FFmpeg/ffprobe are required. From this repository, the existing Python dependencies already provide the core engine. To install an independently runnable package in a separate environment:

```bash
python3 -m venv /path/to/audio2idea-env
/path/to/audio2idea-env/bin/pip install .
# Optional GUI; requires the operating system's tkinter package
/path/to/audio2idea-env/bin/pip install '.[desktop]'
/path/to/audio2idea-env/bin/audio2idea doctor --config /path/to/settings.json --discover
```

These install commands fetch Python packages; model execution stays offline with complete local assets. Do not rerun the legacy installer merely to enable this feature. See the [test matrix](test_matrix.md) and [progress tracker](progress_tracker.md) for actual verification and limitations. Windows/macOS installers, waveform/audio seeking, Word/PDF exports, cloud backends and diarization remain outside this release.

## Troubleshooting

| Symptom | Action |
|---|---|
| New mode selector, prompt editor or colours are missing | Close and reopen the AudioToIdea window to load updated code. The old recorder/tray can continue running. |
| Transcribe + process is disabled after a completed queue | Select a recording and use **Regenerate selected** to run another mode or updated prompt. |
| "Processing failed validation" / partial result | The transcript is retained. Read the error, verify the recording and any edited transcript, then regenerate. Changing the Ollama model or template can improve output; a changed mode/model/template reruns processing with matching ASR reused. |
| A mixed-language summary fails because it dropped नहीं | This is a reproduced qwen2.5:3b quality limitation. The app rejects that result rather than presenting changed approval/payment meaning. Review the original transcript; try regeneration, Clean paragraph or another installed local processing model. |
| Model unavailable or Ollama cannot be inspected | Use **Check setup** or `doctor --check-ollama`; check the configured host and installed local model. |
| Prompt cannot load or has an unknown placeholder | Check the selected file/folder and use `{transcript}` exactly once. The only optional named fields are `{context}` and `{output_language}`. |
| Choosing System does not follow the desktop theme | Select Light or Dark explicitly. Desktop theme reporting varies, especially on Linux. |
| Stop/close waits during inference | It waits for a safe checkpoint. Completed chunks/stages are saved for the next run. |
| Output contains unrelated or manually edited content | Choose a different output folder, or apply transcript corrections through **Save transcript revision**. Overwrite does not remove this protection. |

Latest recorded checks: 24 GUI/legacy tests passed; the full 105-test run had 104 passes and the one mixed-language summary quality failure above. The [verification record](verification.md) preserves the exact commands/results; physical microphone/hotkey and field-audio qualification are still open.
