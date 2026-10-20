# Implementation Steps: Animated Visuals, Next-Level Icons & GUI Modernization

**Plan Reference:** [docs/animated_visuals/plan.md](plan.md)  
**Tracker Reference:** [docs/animated_visuals/progress_tracker.md](progress_tracker.md)

---

## Phase 1: Shared Theme & Styling Foundations
- [x] **Step 1.1**: Update `theme.py` to define shared styling constants (`FIELD = "#181825"`, `BORDER = "#363a4f"`, `PRIMARY = "#89b4fa"`, `PRIMARY_HOVER = "#b4befe"`).
- [x] **Step 1.2**: Modernize `config_gui.py` into modular Card Frames (`_card()`, `_row()`, `_entry()`, `_combobox()`) matching the visual quality of `audio_to_idea/gui.py`.
- [x] **Step 1.3**: Validate `config_gui.py` compilation and ensure all setting saves/loads function without regression.

---

## Phase 2: Next-Level Vector & Animated Visualizer in `main_gui.py`
- [ ] **Step 2.1**: Implement a multi-state visualizer canvas renderer in `main_gui.py` supporting:
  - **State A (`idle`)**: Resting microphone silhouette surrounded by a soft ambient halo.
  - **State B (`listening`)**: Listening Ear 👂 icon with dynamic radiating acoustic wave arcs pulsing with voice timing.
  - **State C (`thinking`)**: Neural Brain 🧠 icon with rotating synapsing particles and glowing orbit.
  - **State D (`success`)**: Emerald flare / sparkle with completion badge.
- [ ] **Step 2.2**: Maintain backward-compatible canvas references (`self.canvas`, `self.indicator`, `self.status_label`, `self.action_btn`, `self.progress`) so legacy and smoke tests continue to pass.
- [ ] **Step 2.3**: Add status badges in `main_gui.py` header (Active ASR profile, ASR backend engine, active mode `Refine`/`Translate`).
- [ ] **Step 2.4**: Implement result card header with quick-copy button and character/word telemetry.

---

## Phase 3: Expressive & Animated Tray Icons in `tray_app.py`
- [ ] **Step 3.1**: Create `icon_generator.py` (or helper in `tray_app.py`) to generate crisp 64x64 RGBA icons using Pillow:
  - Microphone icon for Idle (`#cdd6f4` on `#2a2b3d` pill).
  - Ear 👂 & Acoustic Wave sequence (4 frames) for Recording (`#f38ba8`).
  - Neural Brain 🧠 & Synapse sequence (4 frames) for Processing (`#89b4fa` / `#f9e2af`).
  - Crescent Moon 🌙 for Evening Review (`#a6e3a1`).
- [ ] **Step 3.2**: Implement background frame cycling daemon in `tray_app.py` that animates `self.icon.icon` during active recording and LLM processing at ~8 FPS (125ms per frame).
- [ ] **Step 3.3**: Ensure clean fallback to static icons if the desktop tray server does not support animated pixmap updates.

---

## Phase 4: Optional Handy-Style Floating Desktop HUD Overlay
- [ ] **Step 4.1**: Create `floating_hud.py`:
  - Frameless floating pill window (`overrideredirect(True)`, `attributes("-topmost", True)`).
  - Displays mini animated Ear / Wave during recording.
  - Displays mini animated Brain during AI refinement.
  - Smoothly auto-dismisses upon text paste / completion.
- [ ] **Step 4.2**: Add configuration toggle `"FLOATING_HUD": true/false` in `config.json` and `config_gui.py` (Features tab).

---

## Phase 5: Verification, Benchmarking & Documentation
- [ ] **Step 5.1**: Run full pytest test suite across `tests/audio_to_idea/test_gui.py`, `tests/regression/test_desktop.py`, `tests/test_vram_and_prewarm.py`.
- [ ] **Step 5.2**: Measure CPU utilization of animations to confirm < 0.5% active and 0% idle.
- [ ] **Step 5.3**: Update `docs/CONFIGURATION_GUIDE.md` and `todo_concept.md` with GUI capabilities.
