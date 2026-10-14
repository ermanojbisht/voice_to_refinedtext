# AudioToIdea implementation steps

Created: 2026-10-13  
Status: Implementation underway; checked tasks have supporting automated/inference evidence. Open tasks identify remaining qualification work.

Read the [plan](plan.md), update the [tracker](progress_tracker.md), and use the [test matrix](test_matrix.md) for evidence. Complete dependencies in order. Checkboxes below mean implemented and verified, not merely code written.

## P0 — Establish the working baseline

- [x] P0.1 Record current Git index/worktree state and hashes of runtime files/configs; identify the actual launch interpreter and launch commands. Preserve pre-existing staged/user edits.
- [x] P0.2 Add isolated regression fixtures for main config, review config, vault, review state, logs, streaks, focus words, and subprocess effects. Patch shared review-state paths before invoking tested functions.
- [x] P0.3 Add contract tests for VoiceEngine's existing string transcription/refinement interfaces, language policy, and desktop output feature flags. Stub keyboard, audio, Whisper, HTTP, and subprocess effects as needed.
- [x] P0.4 Cover Review step accumulation/advance/skip/redo, duplicate advance protection, note writing, and settings round-trip preservation. Stub narration/notifications/Telegram.
- [ ] P0.5 Record controlled manual baseline for tray launch/menu, normal recording, refine/translate, main GUI, review dashboard, and narration. Do not send messages or alter real notes merely to test.
- [ ] P0.6 Assemble representative English, Hindi, Hinglish, numbers/units, quiet field audio, long pause, repeated phrase, and final-speech fixtures with annotated expected speech intervals/critical words.
- [x] P0.7 Establish exact reproducible test commands and label tests as fast, audio integration, local-model, desktop/manual, and portability. Record existing failures separately from new regressions.

**Exit check:** T01–T03 have usable baseline evidence; real-model/manual cases are explicitly recorded rather than claimed from static checks. Any blocking baseline failure is resolved or the affected integration work is held.

## P1 — Portable settings and model diagnostics

- [x] P1.1 Create the headless package, typed config/result/error contracts, and versioned JSON example. Keep GUI, microphone, keyboard, and review imports out of core initialization.
- [x] P1.2 Implement and document CLI/environment/file/legacy/default precedence, relative paths, `~`, environment expansion, immutable per-job snapshots, and validation without side effects.
- [x] P1.3 Define documented environment names, including the `ASR_MODEL_PATH` alias, and conflict handling. Add `--config`, `--model`, `--cache-root`, `--revision`, and device overrides.
- [x] P1.4 Resolve direct model directories and Hugging Face repository-cache snapshots; validate format, required assets, broken links, and revisions. Never silently substitute a different explicit model.
- [x] P1.5 Add compatible-model discovery with explicit selection and actionable explanations for raw Transformers weights and invalid `refs/main`.
- [x] P1.6 Add `doctor` and `--help` without model loading/downloads. Report effective settings/provenance, dependencies, model readiness, and optional Ollama readiness.
- [x] P1.7 Add readable configuration comments in code/docstrings and draft GUI labels/help text for all fields; keep local absolute paths out of committed defaults.
- [x] P1.8 Verify the two observed CTranslate2 snapshots and the broken/valid OpenAI snapshots as read-only diagnostic cases. Do not repair or convert weights.

**Exit check:** T04–T07 and headless imports pass; offline/missing-cache errors are useful; portable example and documented overrides agree.

## P2 — Ingestion, preparation, and segmentation

- [x] P2.1 Accept files/folders with deterministic traversal and supported-format validation. Handle unreadable, corrupt, empty, spaced, and Unicode paths.
- [x] P2.2 Create unique per-job temporary directories; probe/decode audio without changing the source, live `input.wav`, or original timestamps.
- [x] P2.3 Produce 16 kHz mono PCM, with configurable optional normalization. Retain silence and duration; handle normalization failures explicitly.
- [x] P2.4 Generate configurable overlapping chunks with precise original-time offsets, including short files, exact boundaries, and tail chunks. No cross-fades.
- [x] P2.5 Add cancellation/cleanup points and document units, resampling choices, and timing invariants in code.
- [ ] P2.6 Compare prepared and original field recordings; use the results to decide whether normalization should remain off by default.

**Exit check:** T08–T09 pass; no missing tail interval or source mutation; preparation quality decisions have actual audio evidence.

## P3 — Structured ASR and transcript exports

- [x] P3.1 Implement local-only faster-whisper loading with complete assets, device/compute validation, CPU threads, and clear auto versus explicit device behavior.
- [x] P3.2 Decode every planned chunk into structured segment/word data; preserve numeric speech, names, units, and mixed-language content. Add separate language policies without changing legacy behavior.
- [x] P3.3 Merge overlapping results using timing and text; maintain original offsets and legitimate repetitions. Keep uncertain boundaries/diagnostics visible.
- [x] P3.4 Persist canonical transcript JSON with source/model/settings identity and chunk coverage; support hour-safe TXT, SRT, VTT, and JSON outputs.
- [x] P3.5 Verify first/middle/last annotated speech, especially after long silence; distinguish coverage verification from recognition accuracy.
- [x] P3.6 Run isolated actual-model tests using the configured CTranslate2 cache, and an available small-model CPU smoke test. Record exact revisions and runtime conditions.
- [x] P3.7 Add documented lifecycle cleanup, progress events, and cancellation; verify no module initialization causes model download or loading.

**Exit check:** T07 and T10–T12 pass with real-model evidence; all planned chunks are accounted for and critical speech/figures have been reviewed.

## P4 — Durable jobs and CLI

- [x] P4.1 Define job/stage states, manifest versioning, workspace location, stage fingerprints, and stable source identity.
- [x] P4.2 Implement atomic outputs/state, per-job cross-process locking, collision-safe naming, and directory structure preservation.
- [x] P4.3 Implement stage-aware skip/resume, overwrite boundaries, interruption recovery, and protection of unrelated or user-edited files.
- [x] P4.4 Expose `transcribe`, `process`, `doctor`, and resume/retry controls through `python -m audio_to_idea`; reserve `watch` for P6. Define exit codes for success, invalid configuration, partial batch failure, and interruption.
- [x] P4.5 Provide honest stage/chunk progress and machine-readable status without mixing logs into JSON output. Avoid unearned percent/ETA precision.
- [x] P4.6 Test one failed file among good files, changed settings/source content, identical stems/extensions, disk-full/permission failures, and cancellation at each durable boundary.
- [x] P4.7 Document commands that are runnable without a display or microphone. Keep `process`'s synthesis status explicit until P5 is delivered.

**Exit check:** T13–T16 pass; reruns are safe, interrupted transcription resumes correctly, and headless CLI works.

## P5 — Domain context and evidence-linked synthesis

- [x] P5.1 Implement profile files containing title, glossary, background, output language, and extraction prompt. Define inline/context-file/profile combination rules.
- [x] P5.2 Apply a bounded glossary to ASR where appropriate and background to synthesis; track profile identity/version in stage fingerprints.
- [x] P5.3 Implement the local Ollama adapter with generation options in the documented request structure, bounded context, timeout, error classification, and model lifecycle controls.
- [x] P5.4 Extract in token-bounded sections and consolidate with evidence IDs retained. Validate the three output sections and source references.
- [x] P5.5 Label spoken proposals versus inferred suggestions; preserve uncertainty and missing owners/dates. Include source duration/model/transcript revision metadata.
- [x] P5.6 Store corrected transcripts as revisions; support regenerating ideas from the selected revision without modifying raw ASR.
- [x] P5.7 Preserve completed transcripts when Ollama fails; implement synthesis-only retry and explicit partial-success status.
- [ ] P5.8 Manually assess local-model output on representative administrative/technical recordings, including misleading context and unsupported claims. Record quality limitations.

**Exit check:** T17–T19 pass; ideas cite valid source segments, long input stays within budget, and no summary failure destroys transcripts.

## P6 — Folder watching

- [x] P6.1 Add `watch` with polling/stability settings and the same job service used by CLI/GUI.
- [x] P6.2 Wait for completed copies; require stable metadata and successful probing, with revalidation before processing.
- [x] P6.3 Ignore generated artifacts/workspaces, deduplicate events, and lock shared jobs across CLI/GUI/watch invocations.
- [x] P6.4 Add bounded retry/backoff, clear corrupt-file status, clean shutdown, and restart recovery without hot loops.
- [x] P6.5 Document polling, recursive scope, output destination, network/removable-drive limitations, and queue behavior.

**Exit check:** T20 passes, including slow copy, duplicate events, restart, and outputs placed within watched directories.

## P7 — Shared resources and compatibility adapters

- [x] P7.1 Review measured startup/VRAM use and define a cross-process resource protocol covering relevant legacy ASR/LLM entry points, cancellation, stale owners, and lock ordering.
- [x] P7.2 Introduce only the required shared services/adapters, preserving legacy public interfaces, filtering/language behavior, error handling, and output effects.
- [x] P7.3 Keep live recording responsive; defer batch inference during live/review work. Release new-job ASR before synthesis when configured. Never unload another process's model silently.
- [x] P7.4 Handle resident-model memory failures and explicit CPU/retry choices. Separate inference serialization from memory ownership.
- [ ] P7.5 Check reminder, narration, morning-brief, and Ollama behavior during batch work; document remaining scheduling limits.
- [x] P7.6 Run legacy baseline before/after and headless CLI tests. Add explanatory comments around compatibility and lock/model lifecycle decisions.

**Exit check:** T01–T03, T16, and T21 pass; existing workflows remain usable with the feature disabled and while jobs are queued/running.

## P8 — GUI, settings, and launch integration

- [x] P8.1 Build the dedicated themed CustomTkinter window over the existing job service. Add file/folder selection, queue, stage status, cancel/retry, and open-output actions.
- [x] P8.2 Add context selection, separate raw/edited transcript and idea views, unsaved-edit handling, and regeneration/export controls.
- [x] P8.3 Add portable model/cache browsing, discovery/revision selection, device/preparation/synthesis/output/watch settings, and a doctor action.
- [x] P8.4 Add meaningful labels, helper text, and tooltips; explain unavailable actions, overwrite, offline mode, normalization, effective overrides, and when settings take effect.
- [x] P8.5 Validate settings before atomic save; preserve unknown keys and both legacy config files. Preserve main config extension keys if its save path is touched.
- [x] P8.6 Add optional tray/main-GUI launch entries using the active interpreter, isolated imports, and no eager model loading. Disabled integration must retain old startup behavior.
- [x] P8.7 Verify worker-to-main-thread events, close/cancel behavior, subprocess lifetime, repeated opens, responsiveness, DPI/resize behavior, keyboard access, and helpful errors.
- [ ] P8.8 Run the full existing-app desktop smoke checklist in a controlled session and record results/screenshots where useful.

**Exit check:** T01–T03 and T22–T24 pass; GUI/CLI results match and settings round trips preserve legacy data.

## P9 — Release, setup on another PC, and rollback

- [x] P9.1 Add minimal packaging and the `audio2idea` entry point while preserving `python -m audio_to_idea` and existing scripts.
- [x] P9.2 Document optional dependencies, compatible CUDA runtime, CPU operation, model/cache selection, offline first run, profiles, output/resume conventions, and troubleshooting.
- [x] P9.3 Verify an isolated clean CPU installation and a model cache at a different path, including spaces/Unicode; demonstrate no source changes are needed.
- [ ] P9.4 Finish the required test matrix and quality review; mark untested OS/device combinations honestly.
- [ ] P9.5 Rehearse disabling integration/reversing only new changes, preserving source audio, generated outputs, personal settings, and existing user edits.
- [x] P9.6 Review code comments, public docstrings, CLI help, GUI labels/tooltips, dependency changes, and release limitations.
- [ ] P9.7 Update README/setup documents and tracker with exact verification evidence; qualify the first release only after all required gates pass.

**Exit check:** T01–T25 are satisfied for the declared Ubuntu release scope; deferred features/platforms are explicitly listed.

## Initial implementation result

All CLI/GUI pipeline capabilities above are delivered. See [verification.md](verification.md) for completed tests. Remaining unchecked tasks concern live-session/field-audio qualification and full rollback rehearsal; they are not silently marked complete.
