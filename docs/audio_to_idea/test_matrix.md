# AudioToIdea test and acceptance matrix

Created: 2026-10-13  
Status: Executable core/GUI/model tests implemented and exercised. See [verification](verification.md) for exact results and the remaining live-session/field-quality checks.

Related: [plan](plan.md), [implementation steps](implementation_steps.md), [progress tracker](progress_tracker.md), [developer guide](developer_guide.md).

## Test isolation rules

Use temporary input/output/config/vault/state/log directories. Patch the legacy module's global state and narration paths before testing its functions. Stub clipboard/keyboard output, notification commands, TTS, timers, microphone streams, and Telegram. Tests must not type into an active window, overwrite `input.wav`, edit personal notes/streaks, modify the cache, or contact external services.

Fast tests use deterministic fake ASR/LLM backends. Audio integration tests run real decoders on small fixtures. Model tests are explicitly selected, local-only, and record backend/model revision/device. GUI/manual tests require an available controlled desktop. No test that was skipped counts as a pass. Report baseline failures separately from regressions.

Network-denial tests cover sockets/HTTP/model-hub calls during processing, not just whether `allow_downloads` is false. Validate complete tokenizer/config assets as well as weights. Offline means no external calls; local Ollama loopback access is expected for synthesis. External endpoints require explicit configuration and a clear departure from offline mode.

## Required checks

| ID | Behavior and test cases | Pass criterion | First gate |
|---|---|---|---|
| T01 | Legacy engine/config contracts: existing model defaults, language/filtering behavior, refine/translate, feature flags, current public APIs. | Existing behavior matches captured baseline; absent module settings do not change the old workflow. | P0, repeat P7–P9 |
| T02 | Review workflow: accumulate, advance, rapid duplicate advance, skip, redo, date-safe note writing, state/locks, isolated wellness output. | Expected isolated note/state changes; no duplicated transitions or writes; legacy signatures/output formats preserved. | P0, repeat P7–P9 |
| T03 | Existing desktop flows: tray/menu/hotkeys, main GUI, dashboard, narration, reminder and morning-brief contracts. | Controlled baseline recorded; integration introduces no new failure. No unauthorized messages or timer changes. | P0, repeat P7–P9 |
| T04 | Config precedence and validation: CLI > env > module file > documented legacy fallback > defaults; aliases, invalid/future schema versions, ranges, missing fields. | Deterministic effective values/provenance; explicit invalid settings produce useful errors and no mutation. | P1 |
| T05 | Path portability: alternate cache root, relative config paths, relative CLI paths, `~`, env expansion, spaces, Unicode, missing drive. | Resolution follows documented base paths; another PC/path requires configuration only. | P1, repeat P9 |
| T06 | Model discovery: compatible CTranslate2 snapshot, raw Transformers snapshot, missing asset, broken symlink, valid/invalid `refs/main`, multiple revisions. | Correct format/revision reported; no arbitrary fallback, conversions, downloads, or cache writes. | P1 |
| T07 | Offline behavior: empty cache, complete cache, absent tokenizer, unavailable model, download prevention. | No external network attempts; complete local model works; incomplete models fail clearly. | P1, repeat P3 |
| T08 | Decoder/preparation: supported formats, corrupt/empty file, unsupported container, mono/stereo and sample-rate variants, optional normalization. | Correct 16 kHz mono result when prepared; original bytes and duration/timeline preserved within documented resampling tolerance; errors isolated. | P2 |
| T09 | Chunking: shorter than one chunk, exact duration multiple, small tail, long silence, non-default overlap, invalid overlap >= chunk size. | Entire source interval covered; offsets accurate; tail retained; no cross-fade or silent time removal. | P2 |
| T10 | Merge: speech across boundary, legitimate repeated words/sentences, disagreement in overlapping hypotheses, empty chunks. | No duplicated boundary speech or over-aggressive deletion; ordered valid offsets and uncertainty retained. | P3 |
| T11 | ASR completeness/quality: annotated English/Hindi/Hinglish, terms, amounts/dates/units, >10-second pause and speech at the end. | Every annotated speech interval reviewed; first/middle/final speech retained; critical figures/terms checked; omissions and quality limits recorded. | P3 |
| T12 | Export/data schema: start/end validity, segment IDs, hour-long timestamps, Unicode, TXT/SRT/VTT/JSON formatting and round trip. | Well-formed outputs; 0 <= start <= end <= source duration within documented tolerance; evidence IDs resolve; raw transcript preserved. | P3 |
| T13 | Idempotency: unchanged rerun, changed source, model/preparation/profile/prompt/export changes, existing unrelated TXT, edited transcript. | Only invalidated stages rerun; unrelated/edited files protected; settings/provenance accurate. | P4 |
| T14 | Crash/cancel recovery: during decode, ASR chunk, export, synthesis; process termination and partial writes. | No success flag for incomplete output; valid completed stages/chunks recover; temp cleanup is scoped to the job. | P4, repeat P5 |
| T15 | Locks/names/storage: two processes same job, same stems across extensions/subfolders, disk full, permission denied, stale ownership. | One owner per job; deterministic non-colliding outputs; clear errors; atomic state; no unrelated overwrite. | P4 |
| T16 | Headless CLI: unset display, no microphone/keyboard/GUI modules, --help/doctor/transcribe/process, mixed-success batch and JSON status. | Runs without desktop initialization; correct exit codes; stdout contract stable; heavy work remains lazy. | P4, repeat P7 |
| T17 | Context profiles and Ideas and actions: glossary, inline/file/profile context, requested output language, section validation, source references. | Three internal categories; only supported headings in the report; valid evidence links; context never masquerades as spoken evidence. | P5 |
| T18 | Long input and grounding: transcript exceeding budget; misleading context; absent owner/date; repeated/conflicting proposals. | Section extraction/consolidation stays within budget; references survive; unsupported claims are rejected/qualified; no invented details. | P5 |
| T19 | Synthesis failures/revisions: Ollama unavailable/timeout/malformed response, corrected transcript, regenerate and synthesis-only retry. | Transcript retained; partial status clear; retry does not repeat ASR; ideas identify the exact transcript revision. | P5 |
| T20 | Watch: slow copy, stable-but-corrupt input, rename, duplicate events, outputs under watched folder, restart/retry/backoff. | Processes only stable decodable sources once per compatible fingerprint; no output loop/hot retry; clean shutdown/restart. | P6 |
| T21 | CPU/GPU resources: auto CPU, explicit unavailable CUDA, multiple clients, resident legacy model, batch plus live/review work and narration. | Honest device selection; no silent change of explicit device; live recording unaffected; contention queued/errors clear; no foreign-model forced unload. | P7 |
| T22 | GUI queue/events: add files/folder, progress, worker errors, cancel/retry, repeated opens, close during processing, resize/DPI. | UI remains responsive; no worker widget access; job lifetime/cancellation explicit; results match CLI core. | P8 |
| T23 | Settings save: AudioToIdea config, unknown keys, existing `config.json`/`review_config.json`, invalid values, running job snapshots. | Atomic valid save; unknown extensions preserved; legacy files unaffected unless explicitly edited; active jobs retain their settings. | P8 |
| T24 | Labels/help/tooltips: model format/cache path, offline, CPU/GPU, normalization, context, overwrite, partial success, effective overrides. | Clear labels/helper text for essential actions; tooltips meaningful; unavailable actions/errors understandable; keyboard access usable. | P8 |
| T25 | Install/rollback: isolated CPU environment, changed cache location, optional dependencies absent, integration disabled, revert only own changes. | Setup works with configuration only; old entry points work; outputs/personal settings and baseline user edits survive rollback. | P9 |

## Extension acceptance checks

These checks cover the user-approved modes and visual updates. Preserve the original T01–T25 identifiers for historical evidence.

| ID | Behavior and test cases | Pass criterion | Tests / status reference |
|---|---|---|---|
| T26 | Clean paragraph default, all mode outputs, CLI/env/file precedence, prompt placeholders/paths, edit at same path, active-job snapshots, transcript-only operation | Separate outputs coexist; malformed templates fail clearly; single-pass substitution; prompt changes regenerate processing with compatible ASR retained | `test_processing_modes.py`; GUI default/editor cases |
| T27 | English/Hindi/mixed processing, requested translation, figures/dates/acronyms/negation, literal speech-only requests, misleading background | Annotated content/language survives processing; invalid generations are rejected after at most one correction; raw ASR and partial-result state remain intact | Unit validation passes; actual mixed-summary quality failure remains open in `verification.md` |
| T28 | Light/Dark/System, blue–green gradient rendering, enabled/disabled button and arrow contrast, minimum size, resize/theme change/destruction | Visible normal/disabled button labels and arrows have at least 4.5:1 contrast; controls fit at 980 × 700; gradient callbacks are owned/cancelled by widgets | `test_gui.py`; screenshot review |
| T29 | User/developer instructions, README links, portable defaults, CLI example flags, template/package assets, current evidence | Documentation links resolve; example configuration validates; CLI flags match the parser; known failures/skips are accurately recorded; runtime/config/source data unchanged by doc-only edits | Documentation consistency/preservation check; guide and wheel checks |

Latest executed gate: 104 passed, 1 mixed-language summary model-quality failure. The 24 GUI/legacy checks passed. See [verification.md](verification.md) for exact commands and limits; a validation rejection protects data but does not turn a failed quality case into a pass.

## Reproduction commands

The working interpreter is `/usr/bin/python3` (3.10.12). Routine reproduction commands:

```bash
python3 -m pytest tests/audio_to_idea tests/regression -m "not local_model and not desktop"
# Requires complete large-v3/turbo/tiny assets and compatible hardware
export AUDIO2IDEA_TEST_CACHE="/path/to/huggingface/hub"
export AUDIO2IDEA_TEST_LLM="qwen2.5:3b"
python3 -m pytest tests/audio_to_idea/test_local_models.py -q
xvfb-run -a -s '-screen 0 1440x1000x24' python3 -m pytest tests/audio_to_idea/test_gui.py tests/regression -q
python3 -m audio_to_idea --help
python3 -m audio_to_idea doctor --config /path/to/audio_to_idea_config.json
python3 -m audio_to_idea transcribe --input /path/to/fixture.wav --config /path/to/audio_to_idea_config.json --output-dir /tmp/audio2idea-check
python3 -m audio_to_idea process --input /path/to/fixture.wav --context-file /path/to/context.md --config /path/to/audio_to_idea_config.json --output-dir /tmp/audio2idea-check
python3 -m audio_to_idea process --input /path/to/fixture.wav --mode concise_summary --prompt-file /path/to/custom_summary.txt --config /path/to/audio_to_idea_config.json --output-dir /tmp/audio2idea-summary-check
```

These interfaces are implemented. Model tests require `AUDIO2IDEA_TEST_CACHE` pointing to complete cached assets. Desktop tests can run with `xvfb-run`. Use a unique isolated output directory per verification run. A test that is skipped for unavailable hardware/assets/desktop is not a pass.

## Evidence required when closing a phase

Record test IDs, exact commands/interpreter, result counts, skipped checks and reasons, model/revision/device for real-model cases, reviewed audio intervals, relevant fixture/output paths, and observed limitations. Manual checks must state what was actually exercised. Mocked success cannot close a real-audio/model/desktop gate.

For recognition accuracy, annotate representative recordings and track critical-word/number retention plus first/middle/final speech. Establish measured baseline and release targets in P0 rather than inventing universal WER/timing thresholds. Fail a completeness case when annotated spoken material is omitted, even if every chunk was processed.
