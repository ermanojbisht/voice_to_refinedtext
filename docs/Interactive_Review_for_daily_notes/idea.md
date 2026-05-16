# Interactive Evening Review — Idea & Vision

## Problem
The current system is excellent for real-time dictation but has no structural support for end-of-day reflective logging. Users returning from work must manually create, open, and organize Obsidian daily notes. There is no guided, step-by-step workflow to capture daily achievements, priorities, and wellness reflections consistently.

## Solution
A **State-Driven Interview Mode** integrated directly into the existing tray app. When activated, the `Ctrl+Alt+V` hotkey pipeline is intercepted — instead of pasting refined text into the active window, it routes each voice response to the correct section of the user's Obsidian Markdown vault, step by step.

## Core Design Principles
- **Zero disruption to normal mode** — if review is not active, the hotkey behaves exactly as before
- **Everything configurable with sensible defaults** — steps, paths, timeouts, refinement per step
- **Append-only file writes** — never overwrite existing Obsidian content
- **Crash-safe** — tray restart mid-review resumes gracefully
- **Fully local & offline** — consistent with the parent project's privacy-first philosophy

## User Flow
1. User clicks "Start Evening Review" from the system tray menu
2. Tray icon turns **green** — visual signal that interview mode is active
3. A desktop notification prompts: *"Step 1/4: Speak today's focus word"*
4. User presses `Ctrl+Alt+V`, speaks their answer
5. Audio is recorded → transcribed → refined by LLM (per-step configurable)
6. Refined text is appended to the correct section of today's Obsidian note
7. Next step notification fires automatically
8. Repeat until all steps complete
9. LLM generates a brief summary, prepended as `### 📋 Summary` in today's note
10. Tray returns to **gray** (idle), review complete notification shown

## Tray Menu — Review Mode
During review, the tray menu changes to show:
- Current step indicator (e.g., "Step 2/4: Achievements")
- Skip This Step
- Redo This Step (deletes last written entry, re-prompts same step)
- Cancel Review

## Safety & Edge Cases
- **Auto-expiry**: State file older than N hours (default: 1hr, configurable) → auto-cancelled, normal mode restored
- **Tray restart**: If state file exists on startup with today's date → resume review at current step; if older → delete and ignore
- **Redo**: Physically removes the last appended block from the Markdown file before re-recording
- **Wellness isolation**: Wellness log step writes to a separate file by default (privacy)

## Phase 2 Vision
AI reads the last N days of notes (N configurable, default 1) before starting the review and generates contextual follow-up questions. Turns the static interview into an intelligent reflection session — *"Yesterday you prioritized the auth fix, did you complete it?"*

## Architecture Overview
```
[Tray Menu: Start Evening Review]
              |
              v
   [review_engine.py: initialize state]
   [Write /tmp/review_state.json]
   [Send Step 1 notification]
              |
   [Ctrl+Alt+V pressed]
              |
              v
   [engine.py: record → transcribe → refine]
              |
              v
   Is /tmp/review_state.json active?
           /       \
         YES        NO
          |          |
   [review_engine.py]   [Default: paste to window]
   [Append to Obsidian]
   [Advance state]
   [Send next notification]
```
