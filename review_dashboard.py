#!/usr/bin/env python3
"""Evening Review Dashboard — live status panel for the review session.

Opens automatically when a review starts (launched by tray_app.py).
Polls /tmp/review_state.json every 500 ms to stay in sync with the tray.
Buttons communicate with the tray via SIGUSR1 (record) or call review_engine
directly (skip / redo / cancel / next-step structuring).
"""
import datetime
import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import review_engine

# Route dashboard logs to the project log file (not stdout)
review_engine.init_logging(script_dir)
review_engine._rlog("=" * 40)
review_engine._rlog(f"[dashboard] Starting (pid={os.getpid()})")

# ── Palette (Catppuccin Mocha) ─────────────────────────────────────────────────
BG      = "#1e1e2e"
SURFACE = "#313244"
OVERLAY = "#45475a"
TEXT    = "#cdd6f4"
SUBTLE  = "#6c7086"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
YELLOW  = "#f9e2af"


class ReviewDashboard:
    def __init__(self, root):
        review_engine._rlog("[dashboard] __init__ start")
        self.root = root
        self.root.title("Evening Review")
        review_engine._rlog("[dashboard] title set")
        self.root.geometry("980x760")
        self.root.minsize(750, 580)
        review_engine._rlog("[dashboard] geometry set")
        self.root.configure(fg_color=BG)
        review_engine._rlog("[dashboard] fg_color configured")
        self.root.resizable(True, True)
        review_engine._rlog("[dashboard] resizable set")

        self.config = review_engine.load_review_config(script_dir)
        review_engine._rlog("[dashboard] config loaded")
        self.steps  = self.config.get("review_steps", [])
        self.is_processing    = False
        self._review_done     = False
        self._last_context_step = -1
        self._engine          = None
        self._last_streak_n   = None          # change-detection guard for streak label
        self._last_step_times = []            # cached from state; used in _show_complete
        # Language currently shown in the right panel brief ("en" or "hi")
        self._ctx_lang        = self.config.get("context_brief_language", "en")
        # True when the right panel is showing the AI brief; False for per-step history
        self._showing_brief   = False

        review_engine._rlog("[dashboard] calling _build_ui")
        self._build_ui()
        review_engine._rlog("[dashboard] _build_ui done, scheduling first poll")
        # Schedule via after() so callbacks run INSIDE mainloop, not before.
        # Calling synchronously here causes CTkButton.configure() to crash Tcl/Tk.
        self.root.after(200, self._poll_state)
        self.root.after(250, self._build_focus_chart)
        review_engine._rlog("[dashboard] __init__ complete")

    # ── Engine (lazy, for LLM structuring only) ────────────────────────────────

    @property
    def engine(self):
        if self._engine is None:
            from engine import VoiceEngine
            self._engine = VoiceEngine(script_dir)
        return self._engine

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        review_engine._rlog("[dashboard] _build_ui: header frame")
        # ── Header bar (full width) ────────────────────────────────────────────
        hdr = ctk.CTkFrame(self.root, fg_color=ACCENT, corner_radius=0, height=50)
        hdr.pack(fill=ctk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🌙 Evening Review", text_color=BG,
                     font=("Inter", 18, "bold")).pack(side=ctk.LEFT, padx=20)
        ctk.CTkLabel(hdr, text="powered by AI Voice Refiner", text_color=BG,
                     font=("Inter", 12)).pack(side=ctk.RIGHT, padx=20)
        self.streak_lbl = ctk.CTkLabel(hdr, text="", text_color=BG,
                                        font=("Inter", 13, "bold"))
        self.streak_lbl.pack(side=ctk.RIGHT, padx=(0, 8))

        # ── Body (two-column split) ────────────────────────────────────────────
        body = ctk.CTkFrame(self.root, fg_color="transparent")
        body.pack(fill=ctk.BOTH, expand=True, padx=8, pady=8)

        # ── Right panel (context sidebar) ─── pack first so left gets remainder
        review_engine._rlog("[dashboard] _build_ui: right panel")
        right_panel = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=8, width=300)
        right_panel.pack(side=ctk.RIGHT, fill=ctk.Y, padx=(8, 4), pady=4)
        right_panel.pack_propagate(False)

        # Right panel: title row
        ctx_hdr = ctk.CTkFrame(right_panel, fg_color="transparent")
        ctx_hdr.pack(fill=ctk.X, padx=10, pady=(8, 0))
        ctk.CTkLabel(ctx_hdr, text="📅 Context", text_color=ACCENT,
                     font=("Inter", 11, "bold")).pack(side=ctk.LEFT)

        # Narration controls — right side of title row
        self.regen_btn = ctk.CTkButton(
            ctx_hdr, text="↺", width=28, height=22, font=("Inter", 13),
            fg_color="transparent", text_color=SUBTLE, hover_color=OVERLAY,
            command=self._regen_brief)
        self.regen_btn.pack(side=ctk.RIGHT, padx=(2, 0))
        self.replay_btn = ctk.CTkButton(
            ctx_hdr, text="🔁", width=28, height=22, font=("Inter", 13),
            fg_color="transparent", text_color=SUBTLE, hover_color=OVERLAY,
            command=self._replay_brief)
        self.replay_btn.pack(side=ctk.RIGHT, padx=(2, 0))
        self.stop_btn = ctk.CTkButton(
            ctx_hdr, text="⏹", width=28, height=22, font=("Inter", 13),
            fg_color="transparent", text_color=SUBTLE, hover_color=OVERLAY,
            command=review_engine.stop_narration)
        self.stop_btn.pack(side=ctk.RIGHT, padx=(2, 0))

        # Right panel: EN/HI language toggle + stats label
        lang_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        lang_row.pack(fill=ctk.X, padx=10, pady=(6, 0))

        self.en_btn = ctk.CTkButton(
            lang_row, text="EN", width=36, height=22, font=("Inter", 10, "bold"),
            corner_radius=4, command=lambda: self._switch_lang("en"))
        self.hi_btn = ctk.CTkButton(
            lang_row, text="HI", width=36, height=22, font=("Inter", 10, "bold"),
            corner_radius=4, command=lambda: self._switch_lang("hi"))
        self.en_btn.pack(side=ctk.LEFT, padx=(0, 4))
        self.hi_btn.pack(side=ctk.LEFT)
        self._refresh_lang_buttons()

        self.ctx_days_lbl = ctk.CTkLabel(lang_row, text="", text_color=SUBTLE,
                                          font=("Inter", 10))
        self.ctx_days_lbl.pack(side=ctk.RIGHT)

        # Right panel content pane — grid so ctx_text and tasks_outer share height cleanly
        review_engine._rlog("[dashboard] _build_ui: content_pane")
        content_pane = ctk.CTkFrame(right_panel, fg_color="transparent")
        content_pane.pack(fill=ctk.BOTH, expand=True)
        content_pane.grid_rowconfigure(0, weight=1)   # ctx_text — expands
        content_pane.grid_rowconfigure(1, weight=0)   # tasks panel — fixed
        content_pane.grid_rowconfigure(2, weight=0)   # focus word chart — fixed
        content_pane.grid_columnconfigure(0, weight=1)

        review_engine._rlog("[dashboard] _build_ui: ctx_text")
        self.ctx_text = ctk.CTkTextbox(content_pane, fg_color="transparent",
                                        text_color=SUBTLE, font=("Inter", 11),
                                        wrap="word", activate_scrollbars=True)
        self.ctx_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=(6, 4))
        self.ctx_text.insert("end", "Analysing last days…")
        self.ctx_text.configure(state="disabled")

        # Tasks panel — shown only when at the carry-forward step
        review_engine._rlog("[dashboard] _build_ui: tasks panel")
        self.tasks_outer = ctk.CTkFrame(content_pane, fg_color=OVERLAY, corner_radius=6)
        ctk.CTkLabel(self.tasks_outer, text="📋 Yesterday's open tasks",
                     text_color=ACCENT, font=("Inter", 10, "bold")).pack(
                     fill=ctk.X, padx=8, pady=(6, 2))
        self.tasks_scroll = ctk.CTkScrollableFrame(
            self.tasks_outer, fg_color="transparent", height=140)
        self.tasks_scroll.pack(fill=ctk.X, padx=4, pady=(0, 6))
        self._tasks_showing = False
        self._last_tasks    = []    # guard: avoid rebuilding when task list unchanged
        self._task_vars     = []    # keep BooleanVar refs alive; cleared on each rebuild
        # Pre-register grid options while hidden; grid_remove() remembers them for grid()
        self.tasks_outer.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        self.tasks_outer.grid_remove()

        # Focus word chart — bottom of right panel, hidden until data available
        self.focus_frame = ctk.CTkFrame(content_pane, fg_color=OVERLAY, corner_radius=6)
        ctk.CTkLabel(self.focus_frame, text="🎯 Focus Trend (7 days)",
                     text_color=ACCENT, font=("Inter", 10, "bold")).pack(
                     fill=ctk.X, padx=8, pady=(6, 2))
        self.focus_canvas = tk.Canvas(self.focus_frame, bg=OVERLAY, highlightthickness=0,
                                      height=4, width=260)
        self.focus_canvas.pack(fill=ctk.X, padx=8, pady=(0, 6))
        self.focus_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        self.focus_frame.grid_remove()

        # ── Left column ───────────────────────────────────────────────────────
        review_engine._rlog("[dashboard] _build_ui: left column")
        left_col = ctk.CTkFrame(body, fg_color="transparent")
        left_col.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        # Subtitle (current step description)
        self.subtitle_var = ctk.StringVar(value="Initialising…")
        ctk.CTkLabel(left_col, textvariable=self.subtitle_var, fg_color="transparent",
                     text_color=TEXT, font=("Inter", 14), anchor="w").pack(
                     fill=ctk.X, padx=16, pady=(8, 4))

        # Progress bar
        review_engine._rlog("[dashboard] _build_ui: progress bar")
        self.prog_canvas = ctk.CTkProgressBar(left_col, height=8, fg_color=OVERLAY,
                                     progress_color=GREEN, corner_radius=4)
        self.prog_canvas.pack(fill=ctk.X, padx=16, pady=(0, 10))
        self.prog_canvas.set(0)

        # Steps list
        review_engine._rlog("[dashboard] _build_ui: CTkScrollableFrame")
        steps_frame = ctk.CTkScrollableFrame(left_col, fg_color="transparent")
        steps_frame.pack(fill=ctk.BOTH, expand=True, padx=8)

        self.row_frames    = []
        self.icon_labels   = []
        self.name_labels   = []
        self.status_labels = []

        for step in self.steps:
            row = ctk.CTkFrame(steps_frame, fg_color=SURFACE, corner_radius=8)
            row.pack(fill=ctk.X, pady=4, padx=4)

            icon_lbl = ctk.CTkLabel(row, text="○", fg_color="transparent", text_color=SUBTLE,
                                font=("Inter", 16), width=40, anchor="center")
            icon_lbl.pack(side=ctk.LEFT, pady=8)

            name_lbl = ctk.CTkLabel(row, text=step["section_name"], fg_color="transparent",
                                text_color=SUBTLE, font=("Inter", 13, "bold"), anchor="w")
            name_lbl.pack(side=ctk.LEFT, fill=ctk.X, expand=True, pady=8)

            status_lbl = ctk.CTkLabel(row, text="Pending", fg_color="transparent",
                                  text_color=SUBTLE, font=("Inter", 12), width=120, anchor="e")
            status_lbl.pack(side=ctk.RIGHT, padx=12, pady=8)

            self.row_frames.append(row)
            self.icon_labels.append(icon_lbl)
            self.name_labels.append(name_lbl)
            self.status_labels.append(status_lbl)

        review_engine._rlog("[dashboard] _build_ui: step rows done, building buttons")
        try:
            # Primary buttons (Record + Next Step)
            review_engine._rlog("[dashboard] _build_ui: btn_row1 frame")
            btn_row1 = ctk.CTkFrame(left_col, fg_color="transparent")
            btn_row1.pack(fill=ctk.X, padx=16, pady=(12, 6))

            review_engine._rlog("[dashboard] _build_ui: record_btn")
            self.record_btn = ctk.CTkButton(
                btn_row1, text="[Rec] Record", command=self._do_record,
                fg_color=ACCENT, text_color=BG, font=("Inter", 14, "bold"),
                hover_color="#b4befe", corner_radius=8, height=40
            )
            self.record_btn.pack(side=ctk.LEFT, expand=True, fill=ctk.X, padx=(0, 8))

            review_engine._rlog("[dashboard] _build_ui: next_btn")
            self.next_btn = ctk.CTkButton(
                btn_row1, text=">> Next Step", command=self._do_next,
                fg_color=GREEN, text_color=BG, font=("Inter", 14, "bold"),
                hover_color="#89dceb", corner_radius=8, height=40, state="disabled"
            )
            self.next_btn.pack(side=ctk.LEFT, expand=True, fill=ctk.X)

            review_engine._rlog("[dashboard] _build_ui: btn_row2 frame")
            # Secondary buttons (Skip, Redo, Cancel)
            btn_row2 = ctk.CTkFrame(left_col, fg_color="transparent")
            btn_row2.pack(fill=ctk.X, padx=16, pady=(0, 16))

            review_engine._rlog("[dashboard] _build_ui: skip_btn")
            self.skip_btn = ctk.CTkButton(
                btn_row2, text=">> Skip", command=self._do_skip,
                fg_color=OVERLAY, text_color=TEXT, font=("Inter", 12),
                hover_color=SURFACE, corner_radius=6, height=32, width=80
            )
            self.skip_btn.pack(side=ctk.LEFT, padx=(0, 8))

            review_engine._rlog("[dashboard] _build_ui: redo_btn")
            self.redo_btn = ctk.CTkButton(
                btn_row2, text="<< Redo", command=self._do_redo,
                fg_color=OVERLAY, text_color=TEXT, font=("Inter", 12),
                hover_color=SURFACE, corner_radius=6, height=32, width=80
            )
            self.redo_btn.pack(side=ctk.LEFT, padx=(0, 8))

            review_engine._rlog("[dashboard] _build_ui: cancel_btn")
            self.cancel_btn = ctk.CTkButton(
                btn_row2, text="X Cancel", command=self._do_cancel,
                fg_color=RED, text_color=BG, font=("Inter", 12, "bold"),
                hover_color="#f5c2e7", corner_radius=6, height=32, width=80
            )
            self.cancel_btn.pack(side=ctk.RIGHT)
            review_engine._rlog("[dashboard] _build_ui: all buttons done")
        except Exception as _btn_exc:
            import traceback as _tb
            review_engine._rlog(
                f"[dashboard] _build_ui EXCEPTION in button creation: {_btn_exc}\n"
                + _tb.format_exc()
            )
            raise

    # ── Language toggle ────────────────────────────────────────────────────────

    @staticmethod
    def _brief_key(lang):
        """Return the state key for the brief in the given language."""
        return "context_brief_en" if lang == "en" else "context_brief_hi"

    def _refresh_lang_buttons(self):
        """Update EN/HI button colours to reflect the active language."""
        for lang, btn in (("en", self.en_btn), ("hi", self.hi_btn)):
            if lang == self._ctx_lang:
                btn.configure(fg_color=ACCENT, text_color=BG)
            else:
                btn.configure(fg_color=OVERLAY, text_color=SUBTLE)

    def _switch_lang(self, lang):
        """Switch right-panel language, re-render brief, and narrate."""
        self._ctx_lang = lang
        self._refresh_lang_buttons()
        if not self._showing_brief:
            return
        state = review_engine._load_state()
        if state is None:
            return
        brief = state.get(self._brief_key(lang)) or state.get("context_brief", "")
        self._set_ctx_text(brief or "No context available.", TEXT if brief else SUBTLE)
        if brief:
            threading.Thread(
                target=review_engine.narrate, args=(brief, self.config), daemon=True).start()

    # ── Live polling ───────────────────────────────────────────────────────────

    def _poll_state(self):
        if self._review_done:
            return
        review_engine._rlog("[dashboard] _poll_state: tick")
        try:
            active, state = review_engine.is_review_active(script_dir)
            if active and state:
                self._update_ui(state)
            else:
                raw_state = review_engine._load_state()
                if raw_state is None:
                    review_engine._rlog("[dashboard] _poll_state: state gone → showing complete")
                    self._show_complete()
                    return
                if not raw_state.get("active", True):
                    review_engine._rlog("[dashboard] _poll_state: active=False → showing complete")
                    self._show_complete()
                    return
                try:
                    started = datetime.datetime.fromisoformat(raw_state["started_at"])
                    expiry_h = self.config.get("review_expiry_hours", 1)
                    if (datetime.datetime.now() - started).total_seconds() / 3600 > expiry_h:
                        review_engine._rlog("[dashboard] _poll_state: expired → showing complete")
                        self._show_complete()
                        return
                except Exception:
                    pass
        except Exception as e:
            import traceback
            review_engine._rlog(f"[dashboard] _poll_state exception: {traceback.format_exc()}")

        self.root.after(500, self._poll_state)

    def _update_ui(self, state):
        if state.get("step_times"):
            self._last_step_times = state["step_times"]
        idx      = state.get("current_step_index", 0)
        total    = len(self.steps)
        awaiting = state.get("awaiting_more", False)
        clips    = len(state.get("accumulated_raw", []))
        remote_processing = state.get("processing", False)
        busy = self.is_processing or remote_processing

        # Subtitle
        if idx < total:
            sname = self.steps[idx]["section_name"]
            clip_str = f" · {clips} clip{'s' if clips != 1 else ''}" if awaiting else ""
            self.subtitle_var.set(f"Step {idx+1} of {total}: {sname}{clip_str}")
        else:
            self.subtitle_var.set(f"All {total} steps complete — wrapping up…")

        # Progress bar
        self.prog_canvas.set(idx / total if total else 0)

        # Step rows
        for i in range(len(self.steps)):
            frame    = self.row_frames[i]
            icon_lbl = self.icon_labels[i]
            name_lbl = self.name_labels[i]
            st_lbl   = self.status_labels[i]

            if i < idx:
                icon_lbl.configure(text="✅", text_color=GREEN)
                name_lbl.configure(text_color=SUBTLE)
                st_lbl.configure(text="Saved", text_color=GREEN)
                frame.configure(fg_color=SURFACE)
            elif i == idx:
                frame.configure(fg_color=OVERLAY)
                name_lbl.configure(text_color=TEXT)
                if busy:
                    icon_lbl.configure(text="⏳", text_color=YELLOW)
                    st_lbl.configure(text="Processing…", text_color=YELLOW)
                elif awaiting:
                    icon_lbl.configure(text="✓", text_color=ACCENT)
                    st_lbl.configure(text=f"{clips} clip{'s' if clips != 1 else ''} · ready", text_color=ACCENT)
                else:
                    icon_lbl.configure(text="🎤", text_color=RED)
                    st_lbl.configure(text="Speak now", text_color=RED)
            else:
                icon_lbl.configure(text="○", text_color=SUBTLE)
                name_lbl.configure(text_color=SUBTLE)
                st_lbl.configure(text="Pending", text_color=SUBTLE)
                frame.configure(fg_color=SURFACE)

        # Streak label in header — only reconfigure when value changes
        streak_n = state.get("streak_current", 0)
        if streak_n != self._last_streak_n:
            self._last_streak_n = streak_n
            self.streak_lbl.configure(text=f"🔥 {streak_n}" if streak_n > 0 else "")

        # Right panel
        self._update_context_panel(state)

        # Button states
        self.record_btn.configure(
            state="disabled" if busy else "normal",
            text="⏳ Processing…" if busy else "🎤 Record",
            fg_color=OVERLAY if busy else ACCENT
        )
        self.next_btn.configure(state="normal" if (awaiting and not busy) else "disabled")
        self.skip_btn.configure(state="disabled" if busy else "normal")
        self.redo_btn.configure(state="disabled" if busy else "normal")

    def _replay_brief(self):
        threading.Thread(
            target=review_engine.replay_narration, args=(self.config,), daemon=True).start()

    def _regen_brief(self):
        """Bust today's brief cache and regenerate."""
        state = review_engine._load_state()
        if state is None:
            return
        date_str = state.get("date") or datetime.date.today().isoformat()
        review_engine._bust_brief_cache(script_dir, date_str)
        state.pop("context_brief", None)
        state.pop("context_brief_en", None)
        state.pop("context_brief_hi", None)
        state["context_ready"] = False
        review_engine._save_state(state)
        self._last_context_step = -1
        self._showing_brief = False
        self._set_ctx_text("Regenerating…", SUBTLE)
        threading.Thread(
            target=review_engine._run_context_brief,
            args=(script_dir, self.config, dict(state)),
            daemon=True).start()

    def _update_context_panel(self, state):
        """Refresh the right context panel from state. Called from _update_ui."""
        n = self.config.get("last_n_days_context", 3)
        per_step = self.config.get("per_step_context", False)
        idx = state.get("current_step_index", 0)
        notes_data = state.get("context_notes", [])

        if not state.get("context_ready"):
            self._showing_brief = False
            self.ctx_days_lbl.configure(text=f"last {n} days")
            self._set_ctx_text("Analysing last days…", SUBTLE)
            return

        # Always show the AI brief first on initial load, before any per-step content.
        # Without this guard the per-step branch fires immediately at step 0 (because
        # idx=0 != _last_context_step=-1) and the brief is never shown.
        if self._last_context_step == -1:
            self._last_context_step = idx   # arm per-step: fires on next step change
            self._showing_brief = True
            brief = state.get(self._brief_key(self._ctx_lang)) or state.get("context_brief", "")
            found = len(notes_data)
            model = (self.config.get("brief_model")
                     or self.config.get("structure_model")
                     or "default")
            date_str  = state.get("date", "")
            days_part = f"{found} day(s)" if found else f"{n} days"
            self.ctx_days_lbl.configure(text=f"{days_part} · {date_str} · {model}")
            self._set_ctx_text(brief or "No context available.", TEXT if brief else SUBTLE)
            return

        # Carry-forward tasks panel: show at the configured step
        carry_step_id   = self.config.get("carryforward_step_id", 3)
        current_step    = self.steps[idx] if idx < len(self.steps) else None
        at_carry_step   = (self.config.get("carryforward_tasks", False)
                           and current_step
                           and current_step.get("step_id") == carry_step_id)
        tasks           = state.get("carryforward_tasks", [])
        note_date_str   = state.get("carryforward_date", "")

        if at_carry_step and tasks:
            self._show_tasks_panel(tasks, note_date_str)
        else:
            self._hide_tasks_panel()

        if per_step and notes_data and idx < len(self.steps):
            # Per-step: show section-relevant history from past notes
            section_name = self.steps[idx]["section_name"]
            if idx != self._last_context_step:
                self._last_context_step = idx
                self._showing_brief = False
                lines = []
                for note in reversed(notes_data):
                    snippet = review_engine._extract_step_section(section_name, note["content"])
                    if snippet:
                        lines.append(f"{note['date']}: {snippet}")
                if lines:
                    text  = "\n".join(lines)
                    label = f"{section_name} · last {len(notes_data)} day(s)"
                else:
                    text  = f"No {section_name} entries found in last {len(notes_data)} day(s)."
                    label = f"last {len(notes_data)} day(s)"
                self.ctx_days_lbl.configure(text=label)
                self._set_ctx_text(text, TEXT)
        # else: brief already shown and no step change — nothing to update

    # ── Carry-forward task panel ───────────────────────────────────────────────

    def _show_tasks_panel(self, tasks, note_date_str):
        """Populate and reveal the carry-forward checkboxes.
        Skips rebuild if the task list hasn't changed since last render."""
        if self._tasks_showing and self._last_tasks == tasks:
            return  # nothing changed — avoid widget churn every 500ms
        self._last_tasks = list(tasks)
        # Clear old vars first (removes lambda closure refs → allows GC)
        self._task_vars = []
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()
        for task in tasks:
            var = ctk.BooleanVar(value=False)
            self._task_vars.append(var)
            cb = ctk.CTkCheckBox(
                self.tasks_scroll, text=task, variable=var,
                font=("Inter", 11), text_color=TEXT,
                fg_color=ACCENT, hover_color="#b4befe", checkmark_color=BG,
                command=lambda t=task, v=var: self._on_task_checked(t, note_date_str, v)
            )
            cb.pack(fill=ctk.X, padx=4, pady=2, anchor="w")
        if not self._tasks_showing:
            self.tasks_outer.grid()
        self._tasks_showing = True

    def _hide_tasks_panel(self):
        if self._tasks_showing:
            self.tasks_outer.grid_remove()
            self._task_vars = []   # release BooleanVar refs
            self._last_tasks = []
            self._tasks_showing = False

    def _on_task_checked(self, task_text, note_date_str, var):
        if not var.get():
            return  # unchecking — do nothing (can't un-complete a task in vault)
        # Run in background so file I/O doesn't block the UI thread
        def _do_mark():
            ok = review_engine._mark_task_done(script_dir, self.config, task_text, note_date_str)
            if not ok:
                self.root.after(0, lambda: (
                    var.set(False),
                    messagebox.showwarning(
                        "Vault update failed",
                        f"Could not mark task done in vault.\n"
                        f"Please update manually in Obsidian:\n\n- [x] {task_text}"
                    )
                ))
        threading.Thread(target=_do_mark, daemon=True).start()

    def _build_focus_chart(self):
        """Draw a horizontal bar chart of the last 7 focus words. No-op if disabled or no data."""
        if not self.config.get("focus_word_trend", True):
            return
        counts = review_engine._get_focus_word_counts(script_dir, n=7)
        if not counts:
            return
        max_count = counts[0][1]
        bar_max_w  = 160   # pixels for the longest bar
        bar_x      = 72    # x where all bars start
        bar_gap    = 4     # px between label/bar and bar/count
        row_h      = 18
        canvas_h   = len(counts) * row_h + 4
        self.focus_canvas.configure(height=canvas_h)
        self.focus_canvas.delete("all")
        for i, (word, count) in enumerate(counts):
            y = i * row_h + row_h // 2
            self.focus_canvas.create_text(
                bar_x - bar_gap, y, anchor="e", text=word[:12],
                fill=TEXT, font=("Inter", 9))
            bar_w = max(4, int(bar_max_w * count / max_count))
            self.focus_canvas.create_rectangle(
                bar_x, y - 5, bar_x + bar_w, y + 5,
                fill=ACCENT, outline="")
            self.focus_canvas.create_text(
                bar_x + bar_w + bar_gap, y, anchor="w", text=str(count),
                fill=SUBTLE, font=("Inter", 9))
        self.focus_frame.grid()

    def _set_ctx_text(self, text, color):
        self.ctx_text.configure(state="normal")
        self.ctx_text.delete("1.0", "end")
        self.ctx_text.insert("end", text)
        self.ctx_text.configure(state="disabled", text_color=color)

    def _show_complete(self):
        self._review_done = True
        self._build_focus_chart()
        self.subtitle_var.set("✅ Evening Review complete!")
        for i in range(len(self.steps)):
            self.icon_labels[i].configure(text="✅", text_color=GREEN)
            self.name_labels[i].configure(text_color=SUBTLE)
            if i < len(self._last_step_times):
                time_str = f" · {review_engine._fmt_duration(self._last_step_times[i])}"
            else:
                time_str = ""
            self.status_labels[i].configure(text=f"Done{time_str}", text_color=GREEN)
            self.row_frames[i].configure(fg_color=SURFACE)
        self.prog_canvas.set(1.0)
        for btn in (self.record_btn, self.next_btn, self.skip_btn, self.redo_btn):
            btn.configure(state="disabled")
        self.cancel_btn.configure(
            text="Close", fg_color=OVERLAY, text_color=TEXT,
            command=self.root.destroy
        )

    # ── Actions ────────────────────────────────────────────────────────────────

    def _do_record(self):
        """Signal the tray app to start/stop recording via SIGUSR1."""
        try:
            result = subprocess.run(
                ["pkill", "-USR1", "-f", "tray_app.py"],
                capture_output=True
            )
            if result.returncode != 0:
                messagebox.showwarning(
                    "Tray not found",
                    "Could not signal tray_app.py.\n"
                    "Use Ctrl+Alt+V if the tray is running."
                )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _do_next(self):
        if self.is_processing:
            return
        state = review_engine._load_state()
        if state is None:
            return
        if state.get("processing"):
            messagebox.showinfo("Busy", "Processing is already underway — please wait.")
            return
        self.is_processing = True
        self._update_ui(state)
        threading.Thread(
            target=self._structure_and_advance,
            args=(state,),
            daemon=True
        ).start()

    def _structure_and_advance(self, state):
        acquired_lock = False
        try:
            fresh_state = review_engine._load_state()
            if fresh_state is None:
                return
            if fresh_state.get("processing"):
                return
            fresh_state["processing"] = True
            review_engine._save_state(fresh_state)
            acquired_lock = True
            state = fresh_state

            step = review_engine.get_current_step(state, self.config)
            if step is None:
                return
            raw_list     = state.get("accumulated_raw", [])
            raw_combined = "\n".join(raw_list).strip()

            if not raw_combined:
                review_engine.skip_step(script_dir, state, self.config)
            else:
                if step.get("refine", True):
                    tmpl = step.get("structure_prompt", "Reformat as clear bullet points:\n{raw_text}")
                    full_prompt  = tmpl.replace("{raw_text}", raw_combined)
                    struct_model = self.config.get("structure_model") or None
                    structured   = self.engine.refine_with_prompt(full_prompt, structure_model=struct_model)
                else:
                    structured = raw_combined

                state["accumulated_raw"] = []
                state["awaiting_more"]   = False
                review_engine.write_step_to_note(
                    script_dir, self.config, step, structured, state
                )
                review_engine.advance_step(script_dir, state, self.config)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Structuring error", str(e)[:200]
            ))
        finally:
            if acquired_lock:
                final_state = review_engine._load_state()
                if final_state is not None:
                    final_state.pop("processing", None)
                    review_engine._save_state(final_state)
            self.is_processing = False

    def _do_skip(self):
        state = review_engine._load_state()
        if state is None:
            return
        if state.get("processing"):
            messagebox.showinfo("Busy", "Processing is underway — please wait.")
            return
        review_engine.skip_step(script_dir, state, self.config)
        still_active, _ = review_engine.is_review_active(script_dir)
        if not still_active:
            self._show_complete()

    def _do_redo(self):
        state = review_engine._load_state()
        if state is None:
            return
        if state.get("processing"):
            messagebox.showinfo("Busy", "Processing is underway — please wait.")
            return
        review_engine.redo_step(script_dir, state, self.config)

    def _do_cancel(self):
        review_engine._rlog("[dashboard] _do_cancel called")
        state = review_engine._load_state()
        if state and state.get("processing"):
            messagebox.showinfo("Busy", "Processing is underway — cannot cancel right now.")
            return
        if messagebox.askyesno(
            "Cancel Review",
            "Cancel the Evening Review?\nAll progress so far is saved."
        ):
            review_engine._rlog("[dashboard] cancel confirmed by user")
            review_engine.cancel_review(script_dir)
            self.root.destroy()


def main():
    import sys as _sys
    import traceback as _tb_mod

    def _excepthook(exc_type, exc_val, exc_tb):
        msg = "".join(_tb_mod.format_exception(exc_type, exc_val, exc_tb))
        review_engine._rlog(f"[dashboard] UNHANDLED EXCEPTION:\n{msg}")
        _sys.__stderr__.write(f"[dashboard] UNHANDLED EXCEPTION:\n{msg}\n")
    _sys.excepthook = _excepthook

    review_engine._rlog("[dashboard] main() started")
    ctk.set_appearance_mode("dark")
    review_engine._rlog("[dashboard] CTk appearance set")
    root = ctk.CTk()
    review_engine._rlog("[dashboard] CTk window created")

    # GNOME Wayland sends WM_DELETE_WINDOW immediately to background-launched
    # windows (focus-stealing prevention). The default tkinter handler calls
    # root.destroy(), silently killing the window before the user sees it.
    # Suppress it NOW — before any CTk widget creation can process events.
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    review_engine._rlog("[dashboard] WM_DELETE_WINDOW suppressed")

    # lift() is safe on Wayland; focus_force() triggers GNOME focus-stealing
    # defenses and can cause the window to be immediately hidden.
    root.lift()
    root.attributes("-topmost", True)
    root.after(3000, lambda: root.attributes("-topmost", False))

    # Route ALL tkinter callback exceptions to the log file, not just stderr,
    # so crashes inside after() callbacks and widget commands are always visible.
    def _report_tk_error(exc, val, tb):
        review_engine._rlog(
            f"[dashboard] tkinter callback exception: {val}\n"
            + "".join(_tb_mod.format_exception(exc, val, tb))
        )
    root.report_callback_exception = _report_tk_error

    review_engine._rlog("[dashboard] building ReviewDashboard")
    try:
        app = ReviewDashboard(root)
    except Exception as _e:
        review_engine._rlog(
            f"[dashboard] CRASH in ReviewDashboard.__init__: {_e}\n"
            + _tb_mod.format_exc()
        )
        raise
    review_engine._rlog("[dashboard] ReviewDashboard built, entering mainloop")

    def _bind_close():
        root.protocol("WM_DELETE_WINDOW", app._do_cancel)
    root.after(2000, _bind_close)

    def _heartbeat():
        if not app._review_done:
            review_engine._rlog("[dashboard] heartbeat — alive")
            root.after(5000, _heartbeat)
    root.after(5000, _heartbeat)

    def _wmctrl_focus():
        try:
            subprocess.run(["wmctrl", "-a", "Evening Review"],
                           capture_output=True, timeout=2)
        except Exception:
            pass
    root.after(500, _wmctrl_focus)

    root.mainloop()
    review_engine._rlog("[dashboard] mainloop exited")


if __name__ == "__main__":
    main()
