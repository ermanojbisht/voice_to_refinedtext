# AudioToIdea developer guide

Last updated: 2026-10-14.

Start with the [user guide](usage.md), [acceptance matrix](test_matrix.md), [progress tracker](progress_tracker.md) and [executed verification](verification.md). The plan records the initial design; this guide describes the implemented extension.

The default mode is **Clean paragraph**. Concise summary and Ideas and actions remain selectable. The latest full gate has **104 passed, 1 local-model quality failure**; the targeted GUI/legacy gate has **24 passed**. The failing qwen2.5:3b mixed-language summary dropped Hindi negation and was rejected by validation. Live-session, field-audio and rollback qualification remain open. Update the verification record when these results change.

## Entry points and isolation

Run from the repository root:

```bash
python3 -m audio_to_idea --help
python3 -m audio_to_idea process --help
python3 -m audio_to_idea gui
```

Installed entry points are `audio2idea` and `audio2idea-gui`. Python 3.10 or later is required. Processing needs FFmpeg/ffprobe; synthesis needs a running local Ollama service and an installed model. See [installation](usage.md#installation-and-verification) for a separate development environment.

Keep core imports independent of Tk, the microphone, keyboard controllers and legacy review state. `cli.py` imports the GUI only for the `gui` command. ASR weights and Ollama requests are lazy. `transcribe` and `process --no-summary` do not invoke Ollama or load prompt files.

The GUI runs in its own process when launched from the main window/tray. Its launchers use the current Python interpreter. Importing `gui.Tooltip` in the old window must not switch appearance modes or load models.

## Code map

| Files | Responsibility |
|---|---|
| [cli.py](../../audio_to_idea/cli.py), [watcher.py](../../audio_to_idea/watcher.py) | CLI flags/exit codes and stable-copy polling with bounded retries |
| [config.py](../../audio_to_idea/config.py), [models.py](../../audio_to_idea/models.py) | Settings precedence, validation, model resolution/discovery, hardware and diagnostics |
| [audio.py](../../audio_to_idea/audio.py), [transcription.py](../../audio_to_idea/transcription.py), [merging.py](../../audio_to_idea/merging.py) | Temporary audio preparation, timed ASR chunks and conservative overlap merging |
| [jobs.py](../../audio_to_idea/jobs.py), [storage.py](../../audio_to_idea/storage.py) | Shared job orchestration, checkpoint/cache state, ownership, atomic writes and process locks |
| [templates.py](../../audio_to_idea/templates.py), [prompt_templates](../../audio_to_idea/prompt_templates) | Mode names, editable template resolution, safe substitution and content hashes |
| [rewriting.py](../../audio_to_idea/rewriting.py) | Bounded clean-paragraph/summary generation and fidelity checks |
| [synthesis.py](../../audio_to_idea/synthesis.py), [llm.py](../../audio_to_idea/llm.py), [profiles.py](../../audio_to_idea/profiles.py) | Structured idea extraction, local Ollama transport and context/glossary profiles |
| [exports.py](../../audio_to_idea/exports.py) | Transcript TXT/SRT/VTT/JSON rendering |
| [resources.py](../../audio_to_idea/resources.py) | Cross-process inference coordination and legacy recording/inference markers |
| [gui.py](../../audio_to_idea/gui.py), [ui_theme.py](../../audio_to_idea/ui_theme.py) | Queue/editor/settings UI, prompt editor and isolated glass-style theme |

## Shared processing contract

Both interfaces use `JobService.run()`. Its `summary` argument is retained for compatibility: `True` runs the selected processing mode; `False` produces transcript exports only. It returns a result dictionary with `complete`, `partial`, `failed` or `cancelled` status rather than aborting an entire batch.

Processing follows:

```text
settings/source/profile -> prepare -> timed chunks -> ASR -> merge
                                        | checkpointed chunks
                         raw transcript -> optional edited revision -> exports
                                        |
                         selected mode + frozen prompt + local Ollama
                                        |
                         cached processing JSON -> mode-specific text output
```

ASR uses prepared 16 kHz mono samples, overlapping windows, global segment/word timestamps, VAD and `condition_on_previous_text=False`. A profile glossary is passed as the Whisper initial prompt. Background is supplied to Ollama for interpretation and is never treated as spoken evidence. Audio preparation and ASR do not depend on the selected rewriting mode.

Ollama's mode response contracts are:

- **Clean paragraph / Concise summary:** JSON with exactly one string field, `text`. Empty recognised speech skips generation. Nonempty input requires nonempty valid text.
- **Ideas and actions:** JSON arrays `bottlenecks`, `proposals`, `implications`. Each finding contains `text`, cited `evidence` IDs and `kind` (`spoken` or `inferred`). Translated findings also request an original-language `quote`.

`extract()` remains the structured-ideas API for direct callers; the job service explicitly selects between `extract()` and `rewrite()`. Runtime schema instructions accompany the editable template. Changing a template's prose cannot replace the response schema.

Rewriting checks scripts, literal numeric figures, day names, technical acronyms and certain negative markers. Translation permits translated day names and scripts. These are conservative mechanical checks, not complete semantic verification. Structured extraction validates IDs, spoken quotations and cross-category duplicates; it also excludes literal speech-only requests/reassurance when every sentence of an item is of that kind. A substantive adjacent sentence must not be discarded by that filter.

Each input section gets at most one correction after validation fails. Transport/inference failures do not silently become successful output. Long text is processed in bounded sections and joined in source order; it is not truncated or assumed to fit one model call. Rewriting must reserve space for protected-token hints and correction instructions as well as the response and schema.

## Settings and template resolution

Effective settings precedence is CLI → environment → module file → limited read-only legacy defaults → `DEFAULTS`. The current schema is version 1. The portable example is [audio_to_idea_config.example.json](../../audio_to_idea_config.example.json); personal settings are Git-ignored.

Relevant synthesis fields:

| Field | Meaning |
|---|---|
| `mode` | `clean_paragraph` (default), `concise_summary`, `ideas_actions` |
| `prompt_file` | Explicit selected-mode template override |
| `prompt_directory` | Folder containing mode-named personal `.txt` templates |
| `output_language` | `source` by default; English/Hindi choices request translation |
| `context_profile` | Optional JSON/text/Markdown background and glossary profile |
| `model`, `host`, `temperature`, `context_tokens`, `timeout_seconds` | Separate Ollama engine settings |

Template precedence is explicit `prompt_file` → the existing mode file in `prompt_directory` → the packaged mode file. A broken/unreadable selected file is an error. A missing custom-folder mode file uses its packaged default. The GUI saves personal copies and protects shipped/legacy prompt folders.

Only `{transcript}`, `{context}` and `{output_language}` are substituted. `{transcript}` is required exactly once. Named unknown placeholders, invalid UTF-8, empty templates and files exceeding 64 KiB are errors. Substitution is a single regex pass: braces inside user data are not recursively evaluated. JSON literal braces remain usable.

Relative file-config paths resolve beside that config; CLI/environment paths resolve from the invocation directory. `update_settings()` merges edited fields with the latest on-disk file, validates against defaults and atomically writes it. Preserve unrelated fields, relative path spelling and unknown extension keys. Do not persist unchanged CLI/environment overrides.

Switching the GUI mode clears its single-file override and retains the per-mode custom folder. New jobs use the current settings and template. A running batch/watch session keeps its template snapshot; a new `JobService` observes later edits.

## Persistence and cache invalidation

Jobs live under `<output>/.audio2idea/<source-path fingerprint>/`. Preserve that directory for resume. The manifest tracks the raw transcript, optional edit, chunks, processed-mode pointers and published-artifact ownership.

- ASR fingerprints include source content, model identity (path/weight size/mtime/config hash), ASR/audio settings and glossary. Changing the glossary can rerun ASR.
- Processing fingerprints include the selected transcript revision, profile, synthesis settings, `PROMPT_VERSION` and template content hash. Editing a file at the same path invalidates processed-output reuse without invalidating matching ASR.
- Bump `PROMPT_VERSION` in `synthesis.py` when programmatic processing/validation semantics change. Template-only edits already change their digest.
- Bump the ASR `pipeline_version` in `jobs.py` if chunk/merge interpretation changes.
- Maintain immutable raw ASR. Transcript editing requires every existing segment ID, creates another revision and clears outdated word timings.

Results expose `transcript_path`; successful processing also exposes `synthesis_mode`, `processed_path` and `synthesis_path`. Outputs are `_clean.txt`, `_summary.txt` or `_idea.txt`; they coexist. Preserve the older manifest `ideas` pointer for structured-mode readers. Metadata records mode, model and prompt digest.

Publishing reserves ownership in the manifest before the atomic write and finalises it afterward. It checks existing bytes against owned hashes. `--overwrite` reruns work but does not permit overwriting unrelated or manually edited outputs. Locks are kernel-owned and release on process exit; do not unlink a lock file held by another client. Keep ownership through failure-state persistence.

## GUI and legacy compatibility

Workers emit queue events; only Tk's main thread touches widgets. Snapshot settings/template before worker launch. Model discovery runs outside Tk's thread. Cancel/close waits for a safe inference checkpoint; it cannot preempt every model call immediately. Do not erase unsaved transcript edits when refreshing results.

`ui_theme.py` owns explicit normal/disabled/hover colours, dropdown/tab styling and debounced gradient drawing. Colours are `(light, dark)` pairs. Native Tk tags/tooltips need a resolved scalar. `GradientFrame` renders a frosted effect within Tk; opaque child widgets do not provide native desktop blur. Cancel its redraw callback on destruction. Test at 980 × 700 and after a theme/size change. Button/arrow tests require at least 4.5:1 contrast.

Keep the root [theme.py](../../theme.py) and old `prompts/` separate. Preserve legacy language policy, numeric filtering, refinement/translation signatures, clipboard/direct typing behavior and Review state. The only shared runtime integration is resource coordination plus optional launch entries.

Legacy recording markers do not wait for batch inference. Pending legacy inference gets priority before the next batch chunk; active inference is not preempted. Serialize via `resources.py`, release only the new worker's own ASR model, and never unload another process's resident model. File-lock serialization alone does not solve GPU memory residency.

## Tests and evidence

From the repository root:

```bash
# Deterministic core/legacy tests; FFmpeg is required for audio fixtures
python3 -m pytest tests -m "not local_model and not desktop" -q

# Controlled GUI and legacy regression gate
xvfb-run -a -s '-screen 0 1440x1000x24' python3 -m pytest tests/audio_to_idea/test_gui.py tests/regression -q

# Explicitly opt into real cached-model tests
export AUDIO2IDEA_TEST_CACHE="/path/to/huggingface/hub"
export AUDIO2IDEA_TEST_LLM="qwen2.5:3b"
python3 -m pytest tests/audio_to_idea/test_local_models.py -q

# Combined gate with the same explicit local assets
xvfb-run -a -s '-screen 0 1440x1000x24' python3 -m pytest tests -q
```

Real ASR cases currently require cached large-v3, turbo and tiny models, compatible CUDA for GPU cases, and local fixture-generation tools. See [test_local_models.py](../../tests/audio_to_idea/test_local_models.py) and [make_audio_fixtures.py](../../tests/make_audio_fixtures.py). Missing `DISPLAY` or the opt-in cache variable causes relevant checks to skip; a skip is not a pass.

[tests/conftest.py](../../tests/conftest.py) isolates module settings and inference resources. Legacy tests stub external effects and redirect state/vault paths. Never replace these with writes to real review notes, Telegram, microphone streams or active-window typing. Real local-model tests can fail on language/content quality even when transport/schema processing works. Record the actual result and preserve the validation gate.

## Extending and packaging

For another mode, update `templates.MODES`, configuration validation, the processing dispatch/output suffix in `jobs.py`, its response validator and a packaged template. Add fake-backed tests for output/cache/resume/CLI/GUI behavior and real annotated quality cases. Update the user guide, matrix and verification record. Preserve the existing mode defaults unless a user-approved change requires otherwise.

Build independently of the old app's installer:

```bash
python3 -m pip wheel . --no-deps --no-build-isolation -w /tmp/audio2idea-dist
```

The build command assumes the declared build dependencies are already installed. `pyproject.toml` includes `example_profiles/*.json` and `prompt_templates/*.txt`; verify new assets are included. Install the wheel in an isolated environment and import from outside this checkout to catch accidental source-tree dependencies. GUI components are optional (`[desktop]`); core CLI imports must work without them.

Before changing shared runtime code, record the starting Git diff/index and relevant file hashes. Verify preservation afterward. Revert only your scoped changes; never reset pre-existing staged edits, model caches, user settings, review state or generated outputs. Full rollback rehearsal remains a separate qualification task.
