# AudioToIdea integration plan

Created: 2026-10-13  
Status: Implementation delivered incrementally; see the tracker for current verification and open qualification checks.  
Delivery: An independently runnable module in this repository, exposed through CLI and the existing desktop app.

## Documents and authority

- [Implementation steps](implementation_steps.md): ordered tasks and phase exit checks.
- [Progress tracker](progress_tracker.md): actual completion, evidence, and outstanding gates.
- [Test and acceptance matrix](test_matrix.md): required behavior and regression checks.
- [Developer guide](developer_guide.md): implemented interfaces, cache/template rules, theme maintenance and extension workflow.
- [Original specification](../../AUDIO_TO_IDEA_UTILITY_SPECIFICATION.md): source requirements and proposed future workbench.

This plan records the accepted integration decision. It supersedes the original specification's standalone-project roadmap and adjusts its cross-fade, model-format, and hardware assumptions. The original specification remains a reference. The original planning delivery changed documentation only; subsequent implementation and verification are recorded in the tracker.

## 1. Goal and delivery boundaries

Process a saved recording or folder into a timestamped transcript and a selected processed output, using local models by default. **Clean paragraph** is now the user-approved default; Concise summary and Ideas and actions are optional modes. Both CLI and GUI use the same processing service, settings validation, job state, and output conventions.

User-approved extensions on 2026-10-14 add editable mode-specific prompt files, a GUI preview/editor and a blue–green glass-style Light/Dark/System interface. Paragraph/summary outputs use a text response contract; the three-category extraction contract applies to Ideas and actions. The [developer guide](developer_guide.md) and [portable example](../../audio_to_idea_config.example.json) document current defaults. Earlier examples below remain valid inputs because missing settings receive those defaults.

Preserve the current Voice Refiner, Evening Review, dashboard, narration, reminders, hotkeys, clipboard output, direct typing, and existing note formats. Integrate incrementally after establishing a regression baseline. The first supported production environment remains Ubuntu; the new core should avoid platform-specific desktop dependencies so additional operating systems can be qualified later.

First release includes configurable local model/cache selection, file and batch transcription, TXT/SRT/VTT/JSON exports, Ollama synthesis, context profiles, interruption recovery, folder watching, and a CustomTkinter window. It also includes configuration diagnostics and a documented CPU setup for another PC.

Later enhancements are synchronized playback/waveforms, a PySide6 workbench if warranted, Word/PDF export, cloud backends, additional ASR backends, speaker diarization, and full Windows/macOS packaging. A rule-based extractor may be added later but must be visibly identified; an LLM failure must never silently turn into a successful-looking rule-based synthesis.

## 2. Current findings and regression risks

| Finding on 2026-10-13 | Consequence for implementation |
|---|---|
| `VoiceEngine` initializes a keyboard controller and imports desktop/microphone dependencies. | New CLI must not construct `VoiceEngine` or require a display, microphone, tray, or clipboard. |
| `VoiceEngine.transcribe()` collapses segments into a string, forces some detected languages, and discards numeric-only segments. | Implement structured transcription for AudioToIdea; preserve legacy behavior until a tested adapter is introduced. Do not copy numeric filtering into the new pipeline. |
| Recording writes to a shared `input.wav`. | New file jobs use unique temporary directories and never overwrite this recording file. |
| `config_gui.py` reconstructs `config.json` when saving main settings. | New settings have their own file. Any later main-config additions need preservation tests before the GUI writes them. |
| Review code uses shared `/tmp` files, POSIX locks, and persistent vault/log/streak state. | New job state has its own namespace; regression tests use temporary state and vaults. |
| Whisper and Ollama may compete for the same GPU, including across processes. | Use one batch worker, model lifecycle controls, and explicit resource coordination before desktop integration. A GUI worker thread alone does not prevent contention. |
| There are staged user changes in `.gitignore`, `review_config.json`, `review_engine.py`, and `streak.json`. | Preserve this exact starting state. Do not reset, unstage, overwrite, or include these changes in an implementation rollback. |
| No repository-level automated regression suite was found; `model_eval` evaluates LLM prompts. | Add focused regression coverage before changing shared runtime behavior. Existing prompt evaluations do not establish ASR completeness or GUI safety. |

Read-only inventory: Python 3.10.12; faster-whisper 1.2.1; CTranslate2 4.7.1; CustomTkinter 5.2.2; pytest 9.0.2. `ffmpeg`, `ffprobe`, and `ollama` are on the current PATH. The project `.venv` is absent. All 16 inspected Python source files parsed successfully. These observations are not model-load or live-app acceptance tests.

## 3. Local model inventory and compatibility

Observed cache root: `/media/manoj/F1/huggingface_cache/hub/`.

| Cached repository | Observed snapshot | Format and selection |
|---|---|---|
| `Systran/faster-whisper-large-v3` | `edaa852ec7e145841d8ffdb056a99866b5f0a478` | CTranslate2 `model.bin`; no broken links found. Candidate for full large-v3 transcription. |
| `mobiuslabsgmbh/faster-whisper-large-v3-turbo` | `0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf` | CTranslate2 `model.bin`; no broken links found. Candidate for turbo transcription. |
| `openai/whisper-large-v3` | `6cdf07a7e3ec3806e5d55f787915b85d4cd020b1` | Transformers `model.safetensors`; no broken links found. Requires a compatible backend or a separately managed conversion. |
| `openai/whisper-large-v3` (`refs/main`) | `06f233fe06e710322aca913c1bc4249a0d71fce1` | All 11 snapshot entries are broken symlinks in the observed environment. Must fail validation with a useful diagnostic. |

Neither repository cache roots nor arbitrary Transformers weights are directly equivalent to a CTranslate2 model directory. Resolve a compatible snapshot and validate readable weights, configuration, tokenizer, and backend-specific assets before loading. `preprocessor_config.json` is optional for older models that use faster-whisper feature defaults; broken links or malformed optional files remain errors. Existing caches are read-only inputs: no repair, conversion, download, deletion, or rewriting occurs during discovery or normal processing.

Initial backend is `faster-whisper`, using already converted weights. A user selecting raw OpenAI/Transformers weights sees a format explanation and compatible choices. Supporting that format directly or converting it is a separately scoped follow-up. Directory checks establish availability only; real model loading is a later acceptance gate.

## 4. Proposed architecture

```text
CLI commands                  CustomTkinter AudioToIdea window
      \                         /
       configuration + job service + progress events
                          |
 ingest -> prepare -> chunk -> ASR -> merge -> transcript exports
                                      |
                    mode + template snapshot + context
                                      |
                     clean paragraph / concise summary
                       / evidence-linked idea document
```

Module structure (implemented; optional future additions remain in the roadmap):

```text
audio_to_idea/
  __init__.py, __main__.py, cli.py
  config.py, models.py, schemas.py
  audio.py, transcription.py, merging.py
  llm.py, synthesis.py, rewriting.py, profiles.py
  templates.py, prompt_templates/*.txt
  jobs.py, storage.py, exports.py, watcher.py
  resources.py, gui.py, ui_theme.py
audio_to_idea_config.example.json
tests/audio_to_idea/
tests/regression/
```

Keep the processing package independent of `review_engine`, tray state, keyboard controllers, and GUI imports. GUI code stays in `gui.py` and imports the core, never the reverse. Progress is delivered through structured events; workers never update widgets directly. Use small protocols/interfaces for ASR and synthesis to permit fakes in tests and later backends.

Start with additive module code. Reuse existing configuration values through a read-only adapter where explicitly documented. Introduce narrowly scoped shared ASR/resource services only after legacy behavior is covered by tests. Preserve public legacy method signatures and string return values. Do not restructure the entire repository or copy Evening Review's state machine into batch processing.

## 5. Configuration contract

Use versioned JSON, matching the existing application, rather than introducing YAML in the first release. Store module settings in `audio_to_idea_config.json`; ship a portable example file, not personal absolute paths. The actual local profile is machine-specific and should not be committed. GUI saves validate and atomically update this file, preserving unknown supported extension keys.

Precedence, highest first: explicit CLI flags; documented environment overrides; selected module config file; documented read-only legacy values for missing fields; portable defaults. An invalid explicit value is an error, never a reason to silently choose a different model. `--config` selects a settings file; `AUDIO2IDEA_CONFIG` selects it if the flag is absent; otherwise use the repository module settings file if present, then defaults.

ASR selection within that precedence: an explicit snapshot/model directory takes priority over repository ID lookup. Repository lookup uses configured cache root and optional revision. If no cache root is configured, use standard Hugging Face environment/cache conventions. Resolve `refs/main` only when it is complete and compatible. If it is missing/broken, diagnose and list valid candidates; never arbitrarily choose among snapshots. Allow explicit revision selection.

Paths support `~`, documented environment expansion, spaces, Unicode, and relative paths. Paths in a config file are relative to that file; CLI paths are relative to the invocation directory. CLI/environment overrides change only the current run. Resolve paths at runtime, record their provenance, and avoid storing resolved machine paths in portable exports.

Proposed portable starting configuration:

```json
{
  "version": 1,
  "integration": {"enabled": false},
  "asr": {
    "backend": "faster-whisper",
    "model_id": "Systran/faster-whisper-large-v3",
    "model_path": null,
    "cache_root": null,
    "revision": null,
    "device": "auto",
    "compute_type": "auto",
    "cpu_threads": 4,
    "language": "auto",
    "word_timestamps": true,
    "offline": true,
    "allow_downloads": false
  },
  "audio": {
    "sample_rate": 16000,
    "normalize": false,
    "target_lufs": -20.0,
    "true_peak_db": -2.0,
    "chunk_seconds": 60.0,
    "overlap_seconds": 1.5
  },
  "synthesis": {
    "backend": "ollama",
    "host": "http://localhost:11434",
    "model": null,
    "temperature": 0.1,
    "timeout_seconds": 300,
    "context_tokens": 8192,
    "output_language": "source",
    "context_profile": null
  },
  "output": {
    "directory": null,
    "formats": ["txt"],
    "save_metadata": true,
    "overwrite": false
  },
  "jobs": {
    "workers": 1,
    "gpu_busy_policy": "queue",
    "release_asr_before_synthesis": true
  },
  "watch": {"poll_seconds": 2.0, "stable_seconds": 5.0, "recursive": false}
}
```

These fields are implemented; the committed example remains portable. `synthesis.model: null` inherits the existing English Ollama model only if available through the read-only adapter; otherwise `process` requires selection while `transcribe` remains usable. Context budget must be validated against the selected model/runtime. `integration.enabled` controls desktop entry visibility, not explicitly invoked CLI commands. Normalization starts off until real field-audio comparisons justify enabling it; it is not a substitute for noise reduction.

Document flags and environment variables for config path, ASR model path/ID/cache/revision/device/compute type, and Ollama host/model. Preserve the specification's `ASR_MODEL_PATH` alias; reject contradictory aliases rather than resolving them silently. CLI help and GUI must display the effective source of overridden values.

The read-only legacy adapter has a limited contract: missing `asr.model_id` may use `config.json`'s `WHISPER_MODEL` through a documented compatible-model alias map; missing `synthesis.host` may use `OLLAMA_HOST`; missing/null `synthesis.model` may use `OLLAMA_MODELS.en`. A missing legacy file simply supplies no values. Audio preparation, chunk sizes, output paths, and job settings use module defaults, never the live recorder's silence thresholds or Markdown destination. Explicit module configuration always wins.

| Command | Intended behavior | Principal controls |
|---|---|---|
| `transcribe` | Produce transcript artifacts from a file/folder; no synthesis. | `--input`, `--output-dir`, `--format`, `--model`, `--cache-root`, `--revision`, `--device`, `--language`, `--chunk-size`, `--overlap`, `--overwrite`, `--config`. |
| `process` | Transcribe and synthesize, or reuse valid transcript stages. | Transcription controls plus `--context`, `--context-file`, `--profile`, synthesis model/host overrides, and `--no-summary`. |
| `watch` | Monitor a folder and enqueue stable sources through the same processing service. | Processing controls plus stability, polling, and recursive-scope controls. Use this subcommand instead of a duplicate `--watch` mode. |
| `doctor` | Inspect configuration, model assets, and prerequisites without heavy inference. | `--config`, model/cache/device overrides, optional local-service checks, structured output. |

Finalize environment names and help with P1; configure advanced settings through the versioned file even when they have no CLI shortcut. `--model` denotes ASR weights; synthesis uses separately named model controls so the two are never ambiguous.

Local setup example: set only `asr.cache_root` to `/media/manoj/F1/huggingface_cache/hub`, then choose a compatible discovered repository/snapshot. On another PC, change the cache root or model path and choose CPU if no compatible GPU is available. No code changes should be required.

`doctor` reports backend, resolved model, complete/broken assets, effective device/compute type, FFmpeg availability, output writability, and optional Ollama readiness. Diagnostics do not load large models, download anything, or write outputs unless an explicit test is requested. CPU and CUDA are the first supported device choices; MPS requires a different backend and stays deferred. Missing CUDA libraries get a clear explanation and configurable CPU fallback; an explicitly requested CUDA device fails rather than silently changing hardware.

## 6. Processing and data integrity

- Support MP3, WAV, M4A, AAC, FLAC, OGG, and WEBM with decoder validation, actionable errors, and per-file failure isolation.
- Preserve original audio. Use temporary 16 kHz mono PCM when preparation is needed; preserve duration and silence. Optional loudness normalization uses one consistent true-peak target of -2 dB. Do not cross-fade, concatenate overlapping audio, or strip time from the source timeline.
- Chunk with original-time offsets and overlap. Use word timing/text alignment to reconcile boundaries without removing legitimate repeated phrases. Record chunk coverage and uncertain intervals; a completed loop is not proof that every spoken word was recognized.
- Preserve numbers, names, units, Hindi/English switching, and raw ASR text. Store segments with IDs, start/end seconds, text, language information where available, and backend diagnostics. Confidence-like ASR metrics are not calibrated accuracy scores.
- Persist canonical transcript JSON internally even when the requested human-facing format is TXT/SRT/VTT. Include hour-safe timestamps, source identity, selected revision, and processing settings in metadata.
- Keep raw ASR and user-edited transcripts as separate revisions. Ideas identify the transcript revision used and contain evidence segment IDs/timestamps. A context profile is background, not evidence that something was spoken.
- Use the specification's three output sections with consistent headings. Distinguish speaker proposals from model-inferred suggestions, preserve missing/uncertain information, and never invent owners, deadlines, figures, or policy assertions.
- Extract in token-bounded sections, then consolidate with source references intact. A synthesis failure preserves the transcript and marks the job partial/failed; retrying synthesis must not require retranscription.

Outputs retain the source stem: `<stem>.txt` (or requested format), `<stem>_idea.txt`, `<stem>.meta.json`, and canonical state in a module-owned workspace. Directory jobs preserve relative directory structure. Different extensions sharing a stem must be detected before writing and receive deterministic, documented disambiguation. Never overwrite an unrelated TXT or a manually edited transcript just because its stem matches.

Track source content identity and stage-specific fingerprints: ASR model/revision/preparation settings; transcript revision and context/prompt/model settings for synthesis; export settings separately. Mere `.txt` existence is insufficient to skip. Commit files atomically and publish completion only after validating required artifacts. Use per-job locks so CLI, GUI, and watcher cannot process the same source concurrently. Interrupted jobs retain completed chunks/stages where compatible and can resume safely.

Watcher processing requires a stable, decodable file and excludes generated outputs/workspaces. It must avoid duplicate events, hot retry loops, partial-copy processing, and infinite output feedback.

## 7. Desktop integration and resource management

First GUI uses CustomTkinter and the existing theme. Launch it from the tray and main GUI through `sys.executable`, loading no ASR model until a job begins. Run processing outside the UI thread. Provide add files/folder, output selection, job queue, cancel/retry, context profiles, editable transcript, synthesized ideas, export/open-output actions, and clear stage-specific progress.

Add a dedicated AudioToIdea settings page/window with model/cache browsing, compatible-model discovery, revision choice, device, audio settings, synthesis settings, output location, and watch settings. Explain invalid settings inline; saves must not erase existing Voice Refiner/Review configuration. Saving does not silently restart a tray, change active jobs, or change global hotkeys. Jobs use a validated immutable configuration snapshot.

Use explicit labels and persistent helper text for essential choices; tooltips supplement them. Examples: "Model cache folder: where downloaded models are stored", "Offline mode: use downloaded model files only", "Context: background to interpret this recording", and "Normalize volume: may also amplify background noise". Explain overwrite, CPU/GPU fallback, context inheritance, and when a model change applies. Long-running work, disabled actions, errors, partial success, and unsaved transcript edits must be understandable without technical knowledge.

Concurrency has two risks: simultaneous inference and idle models retaining VRAM. Before integration, establish a cross-process coordinator joined by the relevant legacy inference entry points, without changing their results. Defer batch GPU work during live recording/review processing; never interrupt an existing recording. Serialize new batch work and release its ASR model before synthesis when needed. A process-local mutex is insufficient. Detect resource failures and offer explicit CPU/retry guidance; do not repeatedly reload models or forcibly unload a model owned by another process. Regression-check reminders/narration while batch work is active, and document any remaining scheduling limits.

## 8. Phases and gates

| Phase | Deliverable | Required exit evidence |
|---|---|---|
| P0 | Baseline and isolation | Legacy regression checks, representative recording fixtures, sandboxed vault/state, reproduction commands. |
| P1 | Configuration, model discovery, doctor | Precedence, portability, format/broken-link/offline tests; no desktop imports in CLI core. |
| P2 | File preparation and safe chunking | Decoder/normalization/duration/offset/boundary tests on real and synthetic audio. |
| P3 | Transcription service and exports | Complete chunk coverage, timestamps, numeric/Hinglish checks, actual local model and CPU smoke tests. |
| P4 | Jobs, recovery, CLI | File/batch commands, collision/skip/resume/cancel/lock tests and actionable exit codes. |
| P5 | Context profiles and synthesis | Evidence-linked output, long-input handling, hallucination review, partial-failure/retry tests. |
| P6 | Watch mode | Stable-file, duplicate-event, retry/backoff, restart and output-loop tests. |
| P7 | Resource coordination and narrow legacy adapters | Before/after legacy behavior evidence, display-free CLI, resource-contention and startup-cost checks. |
| P8 | GUI and app integration | Responsive queue, safe settings saves, clear labels/tooltips, cancellation and existing-app manual smoke tests. |
| P9 | Packaging, portability, release | Clean CPU setup, configured cache on another location, full required matrix, rollback rehearsal and setup docs. |

Test every executable change. Each phase remains incomplete until its required gates pass or an explicitly deferred scope is recorded. Tests that could write real notes, trigger notifications, type text, send Telegram messages, or alter live state must instead use isolated paths and fakes; final controlled desktop checks are recorded separately. No model download, installer execution, timer modification, or live-app restart is necessary for this planning delivery.

## 9. Code quality and release discipline

Add docstrings for service contracts, schemas, config precedence, and error semantics. Comments must explain why boundary merging, cache resolution, locking, atomic writes, resource release, and legacy compatibility work as they do. Include units and timestamp conventions. Avoid comments that merely repeat code. Review GUI helper text/tooltips as part of each feature's acceptance checks.

Implement in small reviewable changes. Record exact files changed, tests, outcomes, limitations, and rollback instructions in the tracker. Preserve user changes already in the index. Keep dependency additions optional where possible and never upgrade the working environment as an incidental step. First try the installed faster-whisper/CTranslate2 stack; any required compatibility change receives its own isolated verification.

Rollback means disabling new desktop integration, retaining existing entry points/configurations, and reversing only the implementation's own changes. Preserve generated transcripts and personal settings; use the recorded baseline to distinguish existing user edits. Do not use repository-wide reset/checkout operations or delete caches/state as a rollback strategy.

Technical references: [faster-whisper usage](https://github.com/SYSTRAN/faster-whisper#usage), [faster-whisper 1.2.1 model loading](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/transcribe.py), [CTranslate2 hardware support](https://opennmt.net/CTranslate2/hardware_support.html).
