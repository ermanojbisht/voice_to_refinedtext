# AudioToIdea progress tracker

Created: 2026-10-13  
Last updated: 2026-10-14  
Current state: Processing modes and blue–green glass-style GUI delivered. Latest combined gate: 104 passed, 1 local Ollama mixed-summary quality failure; validation blocks the bad result and preserves ASR. Clean CPU packaging was previously verified. Live-session/field-quality qualification remains open.  
Next qualification: controlled live microphone/hotkey/review session and annotated field-audio review. No development/test process is waiting or hung.

Related: [plan](plan.md), [implementation steps](implementation_steps.md), [test matrix](test_matrix.md), [user guide](usage.md), [developer guide](developer_guide.md), [executed verification](verification.md).

## Status rules

- Planned: work and tests have not been completed.
- In progress: work started; required checks remain.
- Verified: implementation and required tests passed, with evidence recorded.
- Blocked: a specific dependency prevents the next task; record it and a resolution.
- Deferred: explicitly outside the current release scope.

Mark a task checkbox only after its implementation and associated checks are verified. Planning completion is not feature completion. A skipped or unrun check is never recorded as passing.

## Planning delivery

- [x] Read the complete original specification and compare it with the current app.
- [x] Record the decision to deliver an independent module within this repository.
- [x] Inspect existing recording/ASR/GUI/configuration/review integration boundaries.
- [x] Inspect compatible model directories and snapshot symlinks without modifying caches.
- [x] Define portable configuration, model-format validation, and missing-cache behavior.
- [x] Define ordered phases, implementation checklists, and acceptance/test gates.
- [x] Include code comment/docstring and GUI label/helper-text/tooltip requirements.
- [x] Record pre-existing staged user changes and baseline static checks.
- [x] Verify the planning documents, example JSON, links, and preservation of runtime files.

## Phase summary

| Phase | Status | Required checks | Completion evidence |
|---|---|---|---|
| P0 — Baseline and isolation | In progress | T01–T03; annotated fixtures and reproduction commands | Baseline captured; 13 legacy checks passed before edits. Controlled legacy windows/menu passed. Physical/live session remains open. |
| P1 — Config/models/doctor | Verified | T04–T07 | Precedence/path/offline/compatibility tests pass; real cache doctor and discovery exercised. Optional preprocessing JSON is correctly recognized. |
| P2 — Audio preparation/chunks | In progress | T08–T09 | Seven containers and synthetic normalization/duration/offset checks passed. Field-audio normalization comparison remains open; default stays off. |
| P3 — Structured ASR/exports | In progress | T07, T10–T12 | Both large GPU models, tiny CPU and deterministic glossary-guided Hindi fixtures passed. Broader field/Hinglish quality qualification remains open. |
| P4 — Jobs/recovery/CLI | Verified | T13–T16 | Reuse, revisions, collisions, protected files, mixed batches, concurrent clients, atomic-write failure and real process-exit checkpoint recovery passed. |
| P5 — Context/synthesis | In progress | T17–T19; repeat T14 | Local model, bounded context/consolidation, strict evidence IDs and real-recording retry passed. Broader domain claim/quality review remains open. |
| P6 — Watch mode | Verified | T20 | Stable-file, duplicate/change detection and bounded retry/backoff tests pass; restart relies on durable stage reuse. |
| P7 — Resources/legacy adapters | In progress | T01–T03, T16, T21 | Legacy regression, controlled windows/menu, nonblocking recording markers, inference locks, priority and CPU/GPU tests passed. Live reminder/narration coexistence remains open. |
| P8 — GUI/app integration | In progress | T01–T03, T22–T24 | Light/Dark/System, compact layout, responsive discovery, edit/settings preservation, queue/editor, launch visibility and active-interpreter tests passed; screenshots reviewed. Real desktop/session qualification remains open. |
| P9 — Release/portability | In progress | All required T01–T25 within declared release scope | Current wheel and clean CPU install with moved Unicode/space cache passed. Optional-GUI dependency guidance verified. Full live qualification/rollback rehearsal remains open. |

Detailed task checkboxes live in [implementation_steps.md](implementation_steps.md); this table summarizes their gates.

## Release checks

- [x] Existing Voice Refiner behavior matches the captured baseline.
- [ ] Existing Evening Review/dashboard/narration/brief/reminder behavior matches baseline.
- [x] CLI works without a display, microphone, keyboard, or GUI initialization.
- [x] Model/cache paths, revisions, and device are configurable without source edits.
- [x] Current complete CTranslate2 snapshots pass real local-model tests.
- [x] Raw OpenAI weights and broken snapshots produce useful compatibility diagnostics.
- [x] Offline execution avoids external requests and implicit downloads.
- [ ] Long pauses, overlap boundaries, tail speech, Hindi/English switching, and figures pass annotated checks.
- [x] Transcript timing and TXT/SRT/VTT/JSON exports are verified.
- [x] Skip/resume/overwrite/collisions/partial failures preserve user data.
- [x] Ideas retain evidence references and survive synthesis-only retries.
- [x] Watch mode avoids partial-copy processing, duplicates, and output loops.
- [ ] Live app remains responsive during batch resource contention.
- [x] Settings saves preserve legacy and unknown configuration fields.
- [x] New code has explanatory comments and public contract docstrings.
- [x] GUI labels/helper text/tooltips and keyboard access have been reviewed.
- [x] A clean CPU setup with a different cache location is verified.
- [ ] Rollback preserves outputs, personal settings, and pre-existing user edits.
- [x] Setup/troubleshooting documentation and evidence log are current.

## Known findings and decisions

| Item | Status | Resolution or next action |
|---|---|---|
| Personal cache root `/media/manoj/F1/huggingface_cache/hub` | Observed | Use in machine-local settings only; no hardcoded production default. |
| Converted large-v3 and turbo snapshots | Verified inference | Both passed local CUDA pause/boundary/tail tests on RTX 3060. |
| OpenAI large-v3 `refs/main` resolves to broken snapshot | Observed | P1 doctor must diagnose; no cache repair performed. Valid alternate snapshot exists in Transformers format. |
| Raw Transformers weights differ from faster-whisper weights | Decided | Initial backend uses converted models. Direct raw-weight support/conversion deferred. |
| Current `.venv` absent; dependencies available in `python3` | Verified | `/usr/bin/python3` (3.10.12) is the working interpreter; no active legacy GUI/tray process was found during baseline capture. Clean packaging uses a separate `/tmp` venv. |
| Existing staged `.gitignore`, review config/engine, streak edits | Preserve | Keep index and files intact; compare with recorded baseline after each change. |
| Main settings GUI reconstructs config | Regression risk | Separate module file; preservation tests required if shared save behavior is changed. |
| Cross-process GPU contention and resident models | Design gate | Measure and coordinate in P7 before enabling desktop integration. |
| Broad >10-second ASR early-exit claim | Validation needed | Use annotated regression cases; do not assume a universal defect or universal chunking fix. |

## Deferred scope

- [ ] PySide6 waveform/playback workbench and sentence-to-audio seeking.
- [ ] Word/PDF export.
- [ ] Cloud synthesis and explicitly labeled rule-based extraction.
- [ ] Raw Transformers/whisper.cpp or Apple GPU ASR backends.
- [ ] Speaker diarization and fully qualified Windows/macOS installers.

These items are outside the first release gates and are not evidence of incomplete core tasks.

## Evidence log

| Date | Scope | Check and result | Limits |
|---|---|---|---|
| 2026-10-13 | Read-only inventory | Inspected specification, engine, tray, main/settings GUI, review interfaces, installation/docs, and Git status. | Did not launch, stop, or reconfigure the running application. |
| 2026-10-13 | Syntax baseline | Parsed 16 existing Python files using `ast.parse`; zero syntax errors. | No imports executed; no application or model behavior proved. |
| 2026-10-13 | Environment inventory | Python 3.10.12; faster-whisper 1.2.1; CTranslate2 4.7.1; CustomTkinter 5.2.2; pytest 9.0.2. FFmpeg/ffprobe/Ollama located. | No installer run, dependency upgrade, GPU probe/load, or network service test. |
| 2026-10-13 | Model assets | Inspected three cache repositories and four snapshots. Two CTranslate2 snapshots and one Transformers snapshot have no broken links; OpenAI `refs/main` snapshot has 11 broken links. | Presence/stat checks, not weight validation or inference. Cache unchanged. |
| 2026-10-13 | Planning verification | Four documents and README links verified; 69 unique implementation tasks; 25 acceptance checks; portable JSON parsed/validated; local links/code fences clean; 16 existing Python files parse. Git index and protected-file hashes unchanged during verification; tracked unstaged change limited to README documentation links. | Documentation delivery only; T01–T25 remain unrun. Verification report: `/tmp/audio_to_idea_planning_verification_20261013.json`. |

## Implementation evidence (2026-10-13 to 2026-10-14)

See [verification.md](verification.md) for commands, actual evidence, preservation checks and remaining qualification.

- Before integration: 13 isolated legacy regression tests passed.
- Combined run: 70 passed, including core, legacy, Xvfb desktop and real local models; dependency deprecation warnings only.
- Final GUI rendering checks: 2 passed. Additional real process-exit/resume check: 1 passed. Current suite contains 71 tests.
- Existing `input.wav`: transcript, ideas and metadata completed; strict schema correction permitted synthesis retry without discarding ASR.
- Clean installed package: current wheel loaded from an independent venv; CPU transcription passed with physically copied model assets at a different Unicode/space path. Missing optional GUI components produced helpful setup guidance.
- Original main/review config, streak, staged review-engine edits and staged index hashes preserved. Separate runtime log entries are retained.
- Controlled tests do not write real vault/state files, send Telegram, type at the cursor, capture the physical microphone, or alter timers.

## GUI review and modernization — 2026-10-14

- [x] Add persistent Light / Dark / System appearance with portable defaults.
- [x] Review both palettes and the expanded-context layout at 980 × 700.
- [x] Add clear recording, transcript and ideas panels, primary/secondary actions and an empty queue explanation.
- [x] Group settings into Models, Audio, Output and Preferences; retain visible help and tooltips.
- [x] Show stage/chunk progress and disable actions that conflict with active processing.
- [x] Run model-cache discovery outside Tk's main thread, including safe window closure during discovery.
- [x] Preserve unsaved edits when the current queue item is clicked again.
- [x] Refresh regenerated results automatically when the editor has no unsaved changes.
- [x] Save only edited settings; preserve relative paths, extension fields and transient overrides.
- [x] Repeat the combined legacy/core/desktop/local-model gate and record its result: 75 passed, no skips, 3 dependency warnings, 29.14 seconds.

Screenshots: `/tmp/audio2idea_modern_light_20261014.png`, `/tmp/audio2idea_modern_dark_20261014.png`, and matching compact-layout captures. GUI/configuration stage: 21 tests passed before the combined gate. The full command and preservation evidence are recorded in [verification.md](verification.md).

## Short-recording synthesis correction — 2026-10-14

User reproduction: `input.wav` says “I think you are fine. Copy my words and tell me.” The old model output copied that sentence into all three report categories. Valid evidence IDs did not establish that these classifications were meaningful.

- [x] Tighten extraction to substantive findings; empty categories are normal and project background cannot supply facts.
- [x] Require spoken items to be excerpts of their cited transcript, preventing prompt/background text from masquerading as spoken evidence.
- [x] Reject the same finding repeated across categories.
- [x] Permit one bounded validation correction; invalid output after that remains a partial result with ASR preserved.
- [x] Render empty results concisely and omit unsupported headings from nonempty reports; keep the three-key structured contract.
- [x] Version the prompt so existing ASR is reused while ideas are regenerated.
- [x] Stage checks: 17 synthesis/jobs/GUI tests passed before the added full-gate regressions.
- [x] Preserve requested output-language translation with an original-language quote; regression passed.
- [x] Repeat the combined gate including the real qwen2.5:3b reproduction: 83 passed, no skips, 3 dependency warnings, 27.54 seconds.
- [x] Regenerate root `input_idea.txt` with the Project review profile: empty findings and concise output. CLI confirmed cached ASR reuse; source audio and transcript hashes unchanged.

## Editable processing modes — 2026-10-14

User-approved extension: Clean paragraph (default), Concise summary, and Ideas and actions, with Hindi/English/mixed-language preservation and editable prompt files. Existing recorder/review prompts and behavior remain separate.

- [x] M1: Add versioned mode configuration, packaged templates, portable custom paths and content validation; test defaults and precedence.
- [x] M2: Add bounded paragraph/summary processing and editable idea template; preserve raw ASR, independent outputs and content-based cache invalidation; test each stage. Initial core gate: 41 passed.
- [x] M3: Add GUI mode selection, prompt editor/preview and CLI flags; test saved preferences, errors and active-job snapshots. Controlled editor/default-mode pipeline and minimum-layout checks passed; screenshot reviewed.
- [x] M4: Verify English, Hindi and mixed text with actual local Ollama, then repeat legacy/core/desktop/model gates. Final gate: 103 passed, no skips, 3 dependency warnings, 33.56 seconds.
- [x] M5: Update usage/tracker, rebuild package and compare original-functionality/source-data hashes. Rebuilt wheel installed without dependency changes in the separate `/tmp` environment; installed imports and all three templates verified outside this checkout.

Root `input.wav` processed successfully using default Clean paragraph with cached ASR. `input_clean.txt` created; original audio/transcript, all legacy runtime/config files in the before-change snapshot and staged diff retain their hashes. Earlier model checks exposed automatic translation, figure corruption and speech-test misclassification; language/figure/date/acronym/negation validation and conservative speech-only filtering were added before the final gate passed. Broader field-audio and live-desktop qualification remain the existing open checks above.

## Blue–green glass-style GUI — 2026-10-14

- [x] Replace implicit button foregrounds with explicit enabled/disabled colours; fix dropdown arrow contrast.
- [x] Add frosted gradient cards, blue–green backdrop, soft borders and rounded header while retaining Light/Dark/System selection.
- [x] Verify main action/arrow contrast of at least 4.5:1 in Light and Dark, including disabled states and recovery to enabled state.
- [x] Debounce gradient painting; handle resize, theme changes and widget destruction without modifying shared application themes.
- [x] Repeat full regression/model/desktop gate and review final compact screenshots: 104 passed, 1 failed, 3 dependency warnings, 37.29 seconds. All GUI/legacy checks passed; local mixed-language summary dropped नहीं and was correctly rejected, also reproduced in a targeted rerun. No processing code or prompt was modified during this visual change.
- [x] Rebuild the independent package and update verification record. Wheel contents verified; preservation/syntax/whitespace checks passed. Final targeted GUI/legacy gate: 24 passed, 3 dependency warnings, 13.76 seconds.

Known quality finding: qwen2.5:3b can drop negation when summarizing mixed Hindi-English, even after one correction. Such a job is partial with its transcript retained. This remains a model-quality qualification item; the failure is not counted as a passing test.

## User/developer documentation — 2026-10-14

- [x] Add a developer guide for architecture, module boundaries, templates/response contracts, cache/version changes, GUI/theme rules, tests and packaging.
- [x] Update the user guide with current controls, glossary/cache behavior and troubleshooting for validation failures and model quality.
- [x] Link both guides from README and the integration plan; record current mode defaults in the plan.
- [x] Extend the acceptance matrix with T26–T29 for processing modes, language/fidelity, gradient/contrast and documentation.
- [x] Verify local links, example settings, CLI flags and runtime/staged-data preservation: 69 local links resolved; 21 CLI examples parsed; portable defaults and all three templates valid; application code/config/source data and staged diff unchanged. Evidence: `/tmp/audio2idea_documentation_verification_20261014.json`.

## Implementation evidence template

For each completed task or phase, append:

```text
Date / task IDs:
Behavior delivered:
Files changed:
Test IDs and exact commands / interpreter:
Results and skipped checks:
Model revision / device / reviewed audio intervals (if applicable):
Evidence paths:
Legacy regression outcome:
Comment/docstring and GUI-help review:
Limitations / next task:
Rollback for this change:
```
