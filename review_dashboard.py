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

import utils as _utils
import review_engine

# Route all logs (dashboard + review_engine) to the project log file
log_path = os.path.join(script_dir, "review_debug.log")
_logger = _utils.get_logger("dashboard", log_path)
review_engine.init_logging(script_dir)
_logger.info("=" * 40)
_logger.info(f"Starting (pid={os.getpid()})")

from theme import BG, SURFACE, OVERLAY, TEXT, SUBTLE, MUTED, ACCENT, GREEN, RED, YELLOW


class _Tooltip:
    """Simple hover tooltip for any tkinter/CTk widget."""

    def __init__(self, widget, text):
        self._widget = widget
        self._text   = text
        self._tip    = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _event=None):
        if self._tip is not None:
            return  # already visible — don't create a second one
        x = self._widget.winfo_rootx() + self._widget.winfo_width() // 2
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self._tip, text=self._text,
            background=SURFACE, foreground=TEXT,
            relief="flat", padx=6, pady=3, font=("Inter", 10),
        ).pack()

    def _hide(self, _event=None):
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


class ReviewDashboard:
    def __init__(self, root):
        _logger.info("[dashboard] __init__ start")
        self.root = root
        self.root.title("Evening Review")
        _logger.info("[dashboard] title set")
        self.root.geometry("980x760")
        self.root.minsize(750, 580)
        _logger.info("[dashboard] geometry set")
        self.root.configure(fg_color=BG)
        _logger.info("[dashboard] fg_color configured")
        self.root.resizable(True, True)
        _logger.info("[dashboard] resizable set")

        self.config = review_engine.load_review_config(script_dir)
        _logger.info("[dashboard] config loaded")
        self.steps  = self.config.get("review_steps", [])
        self._review_done     = False
        self._last_context_step = -1
        self._engine          = None
        self._last_streak_n   = None          # change-detection guard for streak label
        self._last_step_times = []            # cached from state; used in _show_complete
        # Language currently shown in the right panel brief ("en" or "hi")
        self._ctx_lang        = self.config.get("context_brief_language", "en")
        # True when the right panel is showing the AI brief
        self._showing_brief   = False
        # Spinner state for the processing animation
        self._spinner_running = False
        self._spinner_idx     = 0
        self._spinner_after   = None
        # ── Append-only panel state ───────────────────────────────────────────
        self._panel_has_brief      = False   # brief widget appended at top
        self._panel_brief_widget   = None    # ref to brief CTkLabel (for lang switch)
        self._panel_appended_steps = set()   # section_names whose history is appended
        self._panel_widgets        = []      # all non-clip widgets (for selective clear)
        self._clip_rows            = []      # CTkTextbox refs, one per in-progress clip
        self._clip_zone_frame      = None    # container frame for the clip zone
        self._clip_sep_added       = False   # thick separator added only once per step
        self._last_clip_count      = -1      # detect when clips list changes
        self._wrap_after_id        = None    # debounce timer for wraplength updates

        _logger.info("[dashboard] calling _build_ui")
        self._build_ui()
        _logger.info("[dashboard] _build_ui done, scheduling first poll")
        # Schedule via after() so callbacks run INSIDE mainloop, not before.
        # Calling synchronously here causes CTkButton.configure() to crash Tcl/Tk.
        self.root.after(200, self._poll_state)
        self.root.after(250, self._build_focus_chart)
        _logger.info("[dashboard] __init__ complete")

    # ── Engine (lazy, for LLM structuring only) ────────────────────────────────

    @property
    def engine(self):
        if self._engine is None:
            from engine import VoiceEngine
            self._engine = VoiceEngine(script_dir)
        return self._engine

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        _logger.info("[dashboard] _build_ui: header frame")
        # ── Header bar (full width) ────────────────────────────────────────────
        hdr = ctk.CTkFrame(self.root, fg_color=ACCENT, corner_radius=0, height=50)
        hdr.pack(fill=ctk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Evening Review", text_color=BG,
                     font=("Inter", 18, "bold")).pack(side=ctk.LEFT, padx=20)
        ctk.CTkLabel(hdr, text="powered by AI Voice Refiner", text_color=BG,
                     font=("Inter", 12)).pack(side=ctk.RIGHT, padx=20)
        self.streak_lbl = ctk.CTkLabel(hdr, text="", text_color=BG,
                                        font=("Inter", 13, "bold"))
        self.streak_lbl.pack(side=ctk.RIGHT, padx=(0, 8))

        # ── Body (two-column split) ────────────────────────────────────────────
        body = ctk.CTkFrame(self.root, fg_color="transparent")
        body.pack(fill=ctk.BOTH, expand=True, padx=8, pady=8)

        # ── Right panel (single panel — no tabs) ── pack first, expands
        _logger.info("[dashboard] _build_ui: right panel")
        right_panel = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=8)
        right_panel.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=(8, 4), pady=4)

        _ctx_tab = ctk.CTkFrame(right_panel, fg_color="transparent")
        _ctx_tab.pack(fill=ctk.BOTH, expand=True, padx=2, pady=2)

        # ── Context panel header ──────────────────────────────────────────────
        ctx_hdr = ctk.CTkFrame(_ctx_tab, fg_color="transparent")
        ctx_hdr.pack(fill=ctk.X, padx=10, pady=(8, 0))
        ctk.CTkLabel(ctx_hdr, text="Context", text_color=ACCENT,
                     font=("Inter", 11, "bold")).pack(side=ctk.LEFT)

        # Narration controls — right side of title row
        self.regen_btn = ctk.CTkButton(
            ctx_hdr, text="Regen", width=48, height=28, font=("Inter", 12),
            fg_color="transparent", text_color=MUTED, hover_color=OVERLAY,
            command=self._regen_brief)
        self.regen_btn.pack(side=ctk.RIGHT, padx=(3, 0))
        _Tooltip(self.regen_btn, "Regenerate context brief")
        self.replay_btn = ctk.CTkButton(
            ctx_hdr, text="Replay", width=52, height=28, font=("Inter", 12),
            fg_color=SURFACE, text_color=ACCENT, hover_color=OVERLAY,
            command=self._replay_brief)
        self.replay_btn.pack(side=ctk.RIGHT, padx=(3, 0))
        _Tooltip(self.replay_btn, "Replay narration")
        self.stop_btn = ctk.CTkButton(
            ctx_hdr, text="Stop", width=44, height=28, font=("Inter", 12),
            fg_color="transparent", text_color=MUTED, hover_color=OVERLAY,
            command=review_engine.stop_narration)
        self.stop_btn.pack(side=ctk.RIGHT, padx=(3, 0))
        _Tooltip(self.stop_btn, "Stop narration")

        # Context tab: EN/HI language toggle + stats label
        lang_row = ctk.CTkFrame(_ctx_tab, fg_color="transparent")
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
                                          font=("Inter", 11))
        self.ctx_days_lbl.pack(side=ctk.RIGHT)

        # Content pane — ctx_scroll expands; tasks panel and focus chart sit below
        _logger.info("[dashboard] _build_ui: content_pane")
        content_pane = ctk.CTkFrame(_ctx_tab, fg_color="transparent")
        content_pane.pack(fill=ctk.BOTH, expand=True)
        content_pane.grid_rowconfigure(0, weight=1)   # ctx_scroll — expands
        content_pane.grid_rowconfigure(1, weight=0)   # tasks panel — fixed
        content_pane.grid_rowconfigure(2, weight=0)   # focus word chart — fixed
        content_pane.grid_columnconfigure(0, weight=1)

        _logger.info("[dashboard] _build_ui: ctx_scroll")
        self.ctx_scroll = ctk.CTkScrollableFrame(
            content_pane, fg_color="transparent", corner_radius=0)
        self.ctx_scroll.grid(row=0, column=0, sticky="nsew", padx=6, pady=(4, 4))
        self.ctx_scroll.columnconfigure(0, weight=1)
        self._wrap_after_id = None
        self.ctx_scroll.bind("<Configure>", self._on_scroll_resize)

        # Fix: nested widgets (CTkTextbox etc.) consume mousewheel before it
        # reaches the CTkScrollableFrame canvas. Catch at root level instead.
        self.root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.root.bind_all("<Button-4>",   self._on_mousewheel, add="+")
        self.root.bind_all("<Button-5>",   self._on_mousewheel, add="+")

        # Tasks panel — shown only when at the carry-forward step
        _logger.info("[dashboard] _build_ui: tasks panel")
        self.tasks_outer = ctk.CTkFrame(content_pane, fg_color=OVERLAY, corner_radius=6)
        ctk.CTkLabel(self.tasks_outer, text="Open tasks from past days",
                     text_color=ACCENT, font=("Inter", 11, "bold")).pack(
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
        ctk.CTkLabel(self.focus_frame, text="Focus Trend (7 days)",
                     text_color=ACCENT, font=("Inter", 10, "bold")).pack(
                     fill=ctk.X, padx=8, pady=(6, 2))
        self.focus_canvas = tk.Canvas(self.focus_frame, bg=OVERLAY, highlightthickness=0,
                                      height=4, width=260)
        self.focus_canvas.pack(fill=ctk.X, padx=8, pady=(0, 6))
        self.focus_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        self.focus_frame.grid_remove()

        # ── Left column ───────────────────────────────────────────────────────
        _logger.info("[dashboard] _build_ui: left column")
        left_col = ctk.CTkFrame(body, fg_color="transparent", width=650)
        left_col.pack(side=ctk.LEFT, fill=ctk.Y)
        left_col.pack_propagate(False)

        # Subtitle (current step description)
        self.subtitle_var = ctk.StringVar(value="Initialising…")
        ctk.CTkLabel(left_col, textvariable=self.subtitle_var, fg_color="transparent",
                     text_color=TEXT, font=("Inter", 14), anchor="w").pack(
                     fill=ctk.X, padx=16, pady=(8, 4))

        # Progress bar
        _logger.info("[dashboard] _build_ui: progress bar")
        self.prog_canvas = ctk.CTkProgressBar(left_col, height=8, fg_color=OVERLAY,
                                     progress_color=GREEN, corner_radius=4)
        self.prog_canvas.pack(fill=ctk.X, padx=16, pady=(0, 10))
        self.prog_canvas.set(0)

        # Steps list
        _logger.info("[dashboard] _build_ui: CTkScrollableFrame")
        steps_frame = ctk.CTkScrollableFrame(left_col, fg_color="transparent")
        steps_frame.pack(fill=ctk.BOTH, expand=True, padx=8)

        self.row_frames    = []
        self.icon_labels   = []
        self.name_labels   = []
        self.status_labels = []

        for step in self.steps:
            row = ctk.CTkFrame(steps_frame, fg_color=SURFACE, corner_radius=8)
            row.pack(fill=ctk.X, pady=4, padx=4)

            icon_lbl = ctk.CTkLabel(row, text="o", fg_color="transparent", text_color=MUTED,
                                font=("Inter", 16), width=40, anchor="center")
            icon_lbl.pack(side=ctk.LEFT, pady=8)

            name_lbl = ctk.CTkLabel(row, text=step["section_name"], fg_color="transparent",
                                text_color=MUTED, font=("Inter", 14, "bold"), anchor="w")
            name_lbl.pack(side=ctk.LEFT, fill=ctk.X, expand=True, pady=8)

            status_lbl = ctk.CTkLabel(row, text="Pending", fg_color="transparent",
                                  text_color=MUTED, font=("Inter", 12), width=120, anchor="e")
            status_lbl.pack(side=ctk.RIGHT, padx=12, pady=8)

            self.row_frames.append(row)
            self.icon_labels.append(icon_lbl)
            self.name_labels.append(name_lbl)
            self.status_labels.append(status_lbl)

        _logger.info("[dashboard] _build_ui: step rows done, building buttons")
        try:
            # Primary buttons (Record + Next Step)
            _logger.info("[dashboard] _build_ui: btn_row1 frame")
            btn_row1 = ctk.CTkFrame(left_col, fg_color="transparent")
            btn_row1.pack(fill=ctk.X, padx=16, pady=(12, 6))

            _logger.info("[dashboard] _build_ui: record_btn")
            self.record_btn = ctk.CTkButton(
                btn_row1, text="[Rec] Record", command=self._do_record,
                fg_color=ACCENT, text_color=BG, font=("Inter", 14, "bold"),
                hover_color="#b4befe", corner_radius=8, height=40
            )
            self.record_btn.pack(side=ctk.LEFT, expand=True, fill=ctk.X, padx=(0, 8))

            _logger.info("[dashboard] _build_ui: next_btn")
            self.next_btn = ctk.CTkButton(
                btn_row1, text=">> Next Step", command=self._do_next,
                fg_color=GREEN, text_color=BG, font=("Inter", 14, "bold"),
                hover_color="#89dceb", corner_radius=8, height=40, state="disabled"
            )
            self.next_btn.pack(side=ctk.LEFT, expand=True, fill=ctk.X)

            _logger.info("[dashboard] _build_ui: btn_row2 frame")
            # Secondary buttons (Skip, Redo, Cancel)
            btn_row2 = ctk.CTkFrame(left_col, fg_color="transparent")
            btn_row2.pack(fill=ctk.X, padx=16, pady=(0, 16))

            _logger.info("[dashboard] _build_ui: skip_btn")
            self.skip_btn = ctk.CTkButton(
                btn_row2, text=">> Skip", command=self._do_skip,
                fg_color=OVERLAY, text_color=TEXT, font=("Inter", 12),
                hover_color=SURFACE, corner_radius=6, height=32, width=80
            )
            self.skip_btn.pack(side=ctk.LEFT, padx=(0, 8))

            _logger.info("[dashboard] _build_ui: redo_btn")
            self.redo_btn = ctk.CTkButton(
                btn_row2, text="<< Redo", command=self._do_redo,
                fg_color=OVERLAY, text_color=TEXT, font=("Inter", 12),
                hover_color=SURFACE, corner_radius=6, height=32, width=80
            )
            self.redo_btn.pack(side=ctk.LEFT, padx=(0, 8))

            _logger.info("[dashboard] _build_ui: cancel_btn")
            self.cancel_btn = ctk.CTkButton(
                btn_row2, text="X Cancel", command=self._do_cancel,
                fg_color=RED, text_color=BG, font=("Inter", 12, "bold"),
                hover_color="#f5c2e7", corner_radius=6, height=32, width=80
            )
            self.cancel_btn.pack(side=ctk.RIGHT)
            _logger.info("[dashboard] _build_ui: all buttons done")
        except Exception as _btn_exc:
            import traceback as _tb
            _logger.info(
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
        """Switch right-panel language, update brief widget in place, and narrate."""
        self._ctx_lang = lang
        self._refresh_lang_buttons()
        if not self._showing_brief or self._panel_brief_widget is None:
            return
        state = review_engine.load_state()
        if state is None:
            return
        brief = state.get(self._brief_key(lang)) or state.get("context_brief", "")
        self._panel_brief_widget.configure(
            text=brief or "No context available.",
            text_color=TEXT if brief else SUBTLE,
        )
        if brief:
            threading.Thread(
                target=review_engine.narrate, args=(brief, self.config), daemon=True).start()

    # ── Live polling ───────────────────────────────────────────────────────────

    def _poll_state(self):
        if self._review_done:
            return
        try:
            active, state = review_engine.is_review_active(script_dir)
            if active and state:
                self._update_ui(state)
            else:
                raw_state = review_engine.load_state()
                if raw_state is None:
                    _logger.info("[dashboard] _poll_state: state gone → showing complete")
                    self._show_complete()
                    return
                if not raw_state.get("active", True):
                    _logger.info("[dashboard] _poll_state: active=False → showing complete")
                    self._show_complete()
                    return
                try:
                    started = datetime.datetime.fromisoformat(raw_state["started_at"])
                    expiry_h = self.config.get("review_expiry_hours", 1)
                    if (datetime.datetime.now() - started).total_seconds() / 3600 > expiry_h:
                        _logger.info("[dashboard] _poll_state: expired → showing complete")
                        self._show_complete()
                        return
                except Exception:
                    pass
        except Exception as e:
            import traceback
            _logger.info(f"[dashboard] _poll_state exception: {traceback.format_exc()}")

        self.root.after(500, self._poll_state)

    def _update_ui(self, state):
        if state.get("step_times"):
            self._last_step_times = state["step_times"]
        idx      = state.get("current_step_index", 0)
        total    = len(self.steps)
        awaiting     = state.get("awaiting_more", False)
        clips        = len(state.get("accumulated_raw", []))
        synthesising = state.get("synthesising", False)
        busy         = state.get("processing", False) or synthesising

        # Live elapsed time for the current step
        _step_elapsed = ""
        try:
            started = state.get("step_started_at")
            if started:
                secs = int((datetime.datetime.now() -
                            datetime.datetime.fromisoformat(started)).total_seconds())
                _step_elapsed = f" · ⏱ {review_engine.fmt_duration(secs)}"
        except Exception:
            pass

        # Subtitle
        if synthesising:
            self.subtitle_var.set("Secretary is writing your notes — please wait...")
        elif idx < total:
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
                icon_lbl.configure(text="[ok]", text_color=GREEN)
                name_lbl.configure(text_color=SUBTLE)
                st_lbl.configure(text="Saved", text_color=GREEN)
                frame.configure(fg_color=SURFACE)
            elif i == idx:
                frame.configure(fg_color=OVERLAY)
                name_lbl.configure(text_color=TEXT)
                if busy:
                    icon_lbl.configure(text="...", text_color=YELLOW)
                    busy_label = "Writing notes..." if synthesising else "Processing..."
                    st_lbl.configure(text=busy_label, text_color=YELLOW)
                elif awaiting:
                    icon_lbl.configure(text="[v]", text_color=ACCENT)
                    st_lbl.configure(
                        text=f"{clips} clip{'s' if clips != 1 else ''} · ready{_step_elapsed}",
                        text_color=ACCENT)
                else:
                    icon_lbl.configure(text="[rec]", text_color=RED)
                    st_lbl.configure(text=f"Speak now{_step_elapsed}", text_color=RED)
            else:
                icon_lbl.configure(text="o", text_color=MUTED)
                name_lbl.configure(text_color=MUTED)
                st_lbl.configure(text="Pending", text_color=MUTED)
                frame.configure(fg_color=SURFACE)

        # Streak label in header — only reconfigure when value changes
        streak_n = state.get("streak_current", 0)
        if streak_n != self._last_streak_n:
            self._last_streak_n = streak_n
            self.streak_lbl.configure(text=f"Streak: {streak_n}" if streak_n > 0 else "")

        # Right panel
        self._update_context_panel(state)

        # Focus chart hidden during active review — shown only on completion
        self.focus_frame.grid_remove()

        # Button states
        if synthesising:
            record_label = "Writing notes..."
        elif busy:
            record_label = "Processing..."
        else:
            record_label = "[Rec] Record"
        self.record_btn.configure(
            state="disabled" if busy else "normal",
            text=record_label,
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
        self._last_context_step = -1
        self._panel_clear()
        self._panel_add_brief("Regenerating…", SUBTLE)
        self.ctx_days_lbl.configure(text="")
        review_engine.regenerate_brief(script_dir, self.config)

    # ── Processing spinner ────────────────────────────────────────────────────

    _SPINNER_FRAMES = ["|", "/", "-", "\\", "|", "/", "-", "\\", "|", "/"]

    def _start_spinner(self):
        if self._spinner_running:
            return
        self._spinner_running = True
        self._spinner_idx = 0
        self._animate_spinner()

    def _animate_spinner(self):
        if not self._spinner_running:
            return
        frame = self._SPINNER_FRAMES[self._spinner_idx % len(self._SPINNER_FRAMES)]
        self.ctx_days_lbl.configure(text=f"{frame}  Working…")
        self._spinner_idx += 1
        self._spinner_after = self.root.after(120, self._animate_spinner)

    def _stop_spinner(self):
        if not self._spinner_running:
            return
        self._spinner_running = False
        if self._spinner_after is not None:
            self.root.after_cancel(self._spinner_after)
            self._spinner_after = None

    # ── Context panel ─────────────────────────────────────────────────────────

    def _on_mousewheel(self, event):
        """Forward mousewheel events to ctx_scroll canvas (Linux Button-4/5 and Windows delta)."""
        try:
            canvas = self.ctx_scroll._parent_canvas
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            elif event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _on_scroll_resize(self, event=None):
        """Debounced handler: update wraplength of all panel labels when panel width changes."""
        if self._wrap_after_id is not None:
            self.root.after_cancel(self._wrap_after_id)
        self._wrap_after_id = self.root.after(150, self._apply_wraplength)

    def _apply_wraplength(self):
        """Set wraplength on every CTkLabel in ctx_scroll to match current panel width."""
        self._wrap_after_id = None
        try:
            w = self.ctx_scroll.winfo_width()
            if w < 50:
                return
            wrap = max(100, w - 28)
            for widget in self._panel_widgets:
                if isinstance(widget, ctk.CTkLabel):
                    widget.configure(wraplength=wrap)
        except Exception:
            pass

    def _panel_clear(self):
        """Destroy all widgets inside ctx_scroll and reset tracking state."""
        for w in self.ctx_scroll.winfo_children():
            w.destroy()
        self._panel_has_brief      = False
        self._panel_brief_widget   = None
        self._panel_appended_steps = set()
        self._panel_widgets        = []
        self._clip_rows            = []
        self._clip_zone_frame      = None
        self._clip_sep_added       = False
        self._last_clip_count      = -1
        self._showing_brief        = False

    def _panel_add_label(self, text, color, font=("Inter", 13), bold=False, pady=(4, 2)):
        """Add a read-only CTkLabel to ctx_scroll. Returns the widget."""
        weight = "bold" if bold else "normal"
        lbl = ctk.CTkLabel(
            self.ctx_scroll, text=text, text_color=color,
            font=(font[0], font[1], weight),
            anchor="w", justify="left", wraplength=400,
        )
        lbl.pack(fill="x", padx=8, pady=pady)
        self._panel_widgets.append(lbl)
        return lbl

    def _panel_add_separator(self, thick=False):
        """Add a horizontal rule. thick=True for the past/present divider."""
        color  = ACCENT if thick else OVERLAY
        height = 2    if thick else 1
        sep = ctk.CTkFrame(self.ctx_scroll, fg_color=color, height=height, corner_radius=0)
        sep.pack_propagate(False)   # enforce fixed height — empty frame collapses to 0 without this
        sep.pack(fill="x", padx=4, pady=(8, 8))
        self._panel_widgets.append(sep)

    def _panel_add_brief(self, text, color):
        """Append the AI context brief at the current bottom of the scroll panel."""
        lbl = self._panel_add_label(text, color, font=("Inter", 14), pady=(6, 4))
        self._panel_has_brief    = True
        self._panel_brief_widget = lbl
        self._showing_brief      = True

    def _panel_add_history(self, section_name, text):
        """Append a step-history block (section header + past-notes text)."""
        hdr = self._panel_add_label(
            f"{section_name}  ·  history",
            ACCENT, font=("Inter", 13), bold=True, pady=(8, 2))
        self._panel_add_label(text, SUBTLE, font=("Inter", 13), pady=(2, 8))

    def _fit_textbox(self, tb, min_h=60, max_h=600):
        """Resize a CTkTextbox to exactly fit its displayed content."""
        def _do():
            try:
                tb.update_idletasks()
                count = tb._textbox.count("1.0", "end", "displaylines")
                n = int(count[0]) if count else 1
                info = tb._textbox.dlineinfo("1.0")
                line_h = info[3] if info else 22   # px per display line
                h = max(min_h, min(max_h, n * line_h + 14))
                tb.configure(height=h)
            except Exception:
                pass
        self.root.after(150, _do)

    def _panel_scroll_bottom(self):
        """Scroll ctx_scroll to the bottom so newly appended content is visible."""
        self.root.after(150, lambda: self.ctx_scroll._parent_canvas.yview_moveto(1.0))

    def _panel_scroll_top(self):
        """Scroll ctx_scroll to the top."""
        self.root.after(50, lambda: self.ctx_scroll._parent_canvas.yview_moveto(0.0))

    def _rebuild_clip_zone(self, current_step, clips):
        """Tear down and rebuild the in-progress clip widgets at bottom of panel."""
        # Remove old clip zone frame if it exists
        if self._clip_zone_frame is not None:
            try:
                self._clip_zone_frame.destroy()
            except Exception:
                pass
        self._clip_rows       = []
        self._clip_zone_frame = None

        section      = current_step.get("section_name", "")
        is_isolated  = current_step.get("isolate_file", False)
        privacy_note = " — private note" if is_isolated else ""

        # Thick separator before clip zone — added only once per step
        if not self._clip_sep_added:
            self._panel_add_separator(thick=True)
            self._clip_sep_added = True

        # Clip zone container
        zone = ctk.CTkFrame(self.ctx_scroll, fg_color="transparent")
        zone.pack(fill="x", padx=4, pady=(0, 8))
        zone.columnconfigure(0, weight=1)
        self._clip_zone_frame = zone
        self._panel_widgets.append(zone)

        # Section header
        ctk.CTkLabel(
            zone, text=f"[ {section}{privacy_note} — recording ]",
            text_color=ACCENT, font=("Inter", 12, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 6))

        for i, clip_text in enumerate(clips):
            row_frame = ctk.CTkFrame(zone, fg_color=OVERLAY, corner_radius=6)
            row_frame.grid(row=i + 1, column=0, sticky="ew", padx=2, pady=(0, 4))
            row_frame.columnconfigure(0, weight=1)

            tb = ctk.CTkTextbox(
                row_frame, wrap="word", height=76,
                fg_color="transparent", text_color=GREEN,
                font=("Inter", 14), activate_scrollbars=False,
                spacing1=3, spacing2=2, spacing3=3,
            )
            tb.grid(row=0, column=0, sticky="ew", padx=(6, 2), pady=4)
            tb.insert("end", clip_text)
            self._fit_textbox(tb)   # auto-expand height to fit content

            del_btn = ctk.CTkButton(
                row_frame, text="x", width=24, height=24,
                fg_color="transparent", text_color=RED,
                hover_color=SURFACE, font=("Inter", 12, "bold"),
                corner_radius=4,
                command=lambda ci=i: self._delete_clip(ci),
            )
            del_btn.grid(row=0, column=1, padx=(2, 6), pady=4, sticky="n")
            self._clip_rows.append(tb)

        self._panel_scroll_bottom()

    def _clear_clip_zone(self):
        """Remove the clip zone frame (called after step confirmed or redo)."""
        if self._clip_zone_frame is not None:
            try:
                self._clip_zone_frame.destroy()
            except Exception:
                pass
            self._clip_zone_frame = None
        self._clip_rows      = []
        self._clip_sep_added = False

    def _delete_clip(self, clip_idx):
        """Remove clip at clip_idx from state and trigger clip zone rebuild."""
        state = review_engine.load_state()
        if state is None:
            return
        clips = list(state.get("accumulated_raw", []))
        if 0 <= clip_idx < len(clips):
            clips.pop(clip_idx)
            state["accumulated_raw"] = clips
            if not clips:
                state["awaiting_more"] = False
            review_engine._save_state(state)

    def _flush_clip_edits(self):
        """Read edited text from green clip textboxes → write back to state."""
        if not self._clip_rows:
            return
        state = review_engine.load_state()
        if state is None:
            return
        edited = []
        for tb in self._clip_rows:
            try:
                text = tb.get("1.0", "end").strip()
                if text:
                    edited.append(text)
            except Exception:
                pass
        if edited:
            state["accumulated_raw"] = edited
            review_engine._save_state(state)

    # ── Main context panel update (called every 500 ms) ───────────────────────

    def _update_context_panel(self, state):
        """Refresh the right context panel from state."""
        n            = self.config.get("last_n_days_context", 3)
        per_step     = self.config.get("per_step_context", False)
        idx          = state.get("current_step_index", 0)
        notes_data   = state.get("context_notes", [])
        synthesising = state.get("synthesising", False)
        busy         = state.get("processing", False) or synthesising
        awaiting     = state.get("awaiting_more", False)
        clips        = state.get("accumulated_raw", [])
        current_step = self.steps[idx] if idx < len(self.steps) else None
        interview_raw = state.get("interview_raw", {})
        in_progress  = bool(awaiting and clips and current_step)

        # ── Synthesis lock ────────────────────────────────────────────────────
        if synthesising:
            self._stop_spinner()
            self._hide_tasks_panel()
            self._clear_clip_zone()
            self._last_clip_count = -1
            if not self._panel_has_brief:
                self._panel_clear()
                self._panel_add_brief(
                    "Organising your interview into note sections.\n\n"
                    "This may take 30–90 seconds.\n\n"
                    "Please wait — do not close the dashboard.",
                    YELLOW)
                self.ctx_days_lbl.configure(text="Secretary writing notes…")
            return

        # ── Processing / transcribing: spinner ───────────────────────────────
        if busy:
            self._start_spinner()
            return
        else:
            self._stop_spinner()

        # ── Loading: context not ready yet ───────────────────────────────────
        if not state.get("context_ready"):
            if not self._panel_has_brief:
                self._panel_clear()
                self._panel_add_brief("Analysing last days…", SUBTLE)
                self.ctx_days_lbl.configure(text=f"last {n} days")
            return

        # ── Brief: append once at top, never again ────────────────────────────
        if not self._panel_has_brief:
            brief     = state.get(self._brief_key(self._ctx_lang)) or state.get("context_brief", "")
            found     = len(notes_data)
            date_str  = state.get("date", "")
            days_part = f"{found} day(s)" if found else f"{n} days"
            self.ctx_days_lbl.configure(text=f"{days_part} · {date_str}")
            self._panel_add_brief(brief or "No context available.", TEXT if brief else SUBTLE)
            self._panel_scroll_top()

        # ── Per-step history: append once per section (before first recording) ─
        current_step_id = str(current_step.get("step_id", "")) if current_step else ""
        current_in_interview = current_step_id in interview_raw
        if (per_step and current_step and not in_progress and not current_in_interview):
            section_name = current_step["section_name"]
            if section_name not in self._panel_appended_steps:
                self._panel_appended_steps.add(section_name)
                self._last_context_step = idx
                shown = False
                is_isolated = current_step.get("isolate_file", False)
                if is_isolated:
                    n_ctx    = self.config.get("last_n_days_context", 3)
                    date_str = state.get("date") or datetime.date.today().isoformat()
                    iso_notes = review_engine.get_isolated_notes(
                        script_dir, self.config, n_ctx, date_str)
                    if iso_notes:
                        lines = [f"{note['date']}:\n{note['content']}"
                                 for note in reversed(iso_notes)]
                        self._panel_add_separator()
                        self._panel_add_history(section_name, "\n\n".join(lines))
                        shown = True
                elif notes_data:
                    lines = []
                    for note in reversed(notes_data):
                        snippet = review_engine.extract_step_section(
                            section_name, note["content"])
                        if snippet:
                            lines.append(f"{note['date']}:\n{snippet}")
                    if lines:
                        self._panel_add_separator()
                        self._panel_add_history(section_name, "\n\n".join(lines))
                        shown = True
                if shown:
                    self._panel_scroll_bottom()

        # ── Carryforward tasks panel ──────────────────────────────────────────
        self._eval_tasks_panel(state, current_step)

        # ── Clip zone: rebuild only when clip count changes ───────────────────
        n_clips = len(clips) if in_progress else 0
        if n_clips != self._last_clip_count:
            self._last_clip_count = n_clips
            if in_progress and clips:
                # Merge inline edits from existing textboxes with newly added clips.
                # e.g. user edits clip1 text, then records clip2:
                #   edited_existing = [edited_clip1]
                #   clips (from state) = [original_clip1, clip2]
                #   merged = [edited_clip1, clip2]
                edited_existing = []
                for tb in self._clip_rows:
                    try:
                        text = tb.get("1.0", "end").strip()
                        if text:
                            edited_existing.append(text)
                    except Exception:
                        pass
                if edited_existing and len(clips) > len(edited_existing):
                    # New clips were appended to state; preserve edits to old ones
                    merged = edited_existing + list(clips[len(edited_existing):])
                    fresh = review_engine.load_state()
                    if fresh is not None:
                        fresh["accumulated_raw"] = merged
                        review_engine._save_state(fresh)
                    rebuild_clips = merged
                else:
                    rebuild_clips = list(clips)
                self._rebuild_clip_zone(current_step, rebuild_clips)
            else:
                self._clear_clip_zone()

    def _eval_tasks_panel(self, state, current_step):
        """Show or hide the carry-forward task panel based on current step."""
        carry_step_id = self.config.get("carryforward_step_id", 3)
        at_carry = (self.config.get("carryforward_tasks", False)
                    and current_step
                    and current_step.get("step_id") == carry_step_id)
        tasks         = state.get("carryforward_tasks", [])
        note_date_str = state.get("carryforward_date", "")
        if at_carry and tasks:
            self._show_tasks_panel(tasks, note_date_str)
        else:
            self._hide_tasks_panel()

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
            # tasks may be dicts {"text": str, "days_pending": int, "first_seen": str}
            # or plain strings (legacy). Use first_seen as the note date to update.
            if isinstance(task, dict):
                task_text = task["text"]
                days = task.get("days_pending", 1)
                task_date = task.get("first_seen", note_date_str)
                label = f"{task_text}  ({days}d)" if days > 1 else task_text
            else:
                task_text = task
                task_date = note_date_str
                label = task
            var = ctk.BooleanVar(value=False)
            self._task_vars.append(var)
            cb = ctk.CTkCheckBox(
                self.tasks_scroll, text=label, variable=var,
                font=("Inter", 12), text_color=TEXT,
                fg_color=ACCENT, hover_color="#b4befe", checkmark_color=BG,
                command=lambda t=task_text, d=task_date, v=var: self._on_task_checked(t, d, v)
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
            ok = review_engine.mark_task_done(script_dir, self.config, task_text, note_date_str)
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
        counts = review_engine.get_focus_word_counts(script_dir, n=7)
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

    def _show_complete(self):
        self._review_done = True
        self._build_focus_chart()
        self.subtitle_var.set("Evening Review complete!")
        for i in range(len(self.steps)):
            self.icon_labels[i].configure(text="[ok]", text_color=GREEN)
            self.name_labels[i].configure(text_color=SUBTLE)
            if i < len(self._last_step_times):
                time_str = f" · {review_engine.fmt_duration(self._last_step_times[i])}"
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
        state = review_engine.load_state()
        if state is None:
            return
        if not state.get("active", True):
            return  # review already completed or cancelled — stale call, ignore
        if state.get("processing"):
            messagebox.showinfo("Busy", "Processing is already underway — please wait.")
            return

        # Capture clip text and step name BEFORE clearing
        captured_clips = []
        for tb in self._clip_rows:
            try:
                text = tb.get("1.0", "end").strip()
                if text:
                    captured_clips.append(text)
            except Exception:
                pass
        idx = state.get("current_step_index", 0)
        current_step = self.steps[idx] if idx < len(self.steps) else None
        section_name = current_step.get("section_name", "") if current_step else ""

        # Flush any user edits from green clip textboxes before secretary runs
        self._flush_clip_edits()
        # Replace clip zone with a persistent "saved" read-only block
        self._clear_clip_zone()
        self._last_clip_count = -1
        if captured_clips and section_name:
            self._panel_add_separator()
            self._panel_add_label(
                f"[ok] {section_name} — saved", GREEN, font=("Inter", 12), bold=True)
            for clip in captured_clips:
                self._panel_add_label(clip, SUBTLE, font=("Inter", 13), pady=(4, 8))
            self._panel_scroll_bottom()

        threading.Thread(
            target=self._structure_and_advance,
            args=(state,),
            daemon=True
        ).start()

    def _structure_and_advance(self, _state):
        """Delegate to review_engine.structure_and_advance; dashboard handles UI feedback only."""
        try:
            success, error, still_active = review_engine.structure_and_advance(
                script_dir, self.engine, self.config
            )
            if error:
                self.root.after(0, lambda: messagebox.showerror("Structuring error", error[:200]))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Structuring error", str(e)[:200]))

    def _do_skip(self):
        state = review_engine.load_state()
        if state is None:
            return
        if not state.get("active", True):
            return  # review already completed or cancelled — stale call, ignore
        if state.get("processing"):
            messagebox.showinfo("Busy", "Processing is underway — please wait.")
            return
        review_engine.skip_step(script_dir, state, self.config)
        still_active, _ = review_engine.is_review_active(script_dir)
        if not still_active:
            self._show_complete()

    def _do_redo(self):
        state = review_engine.load_state()
        if state is None:
            return
        if not state.get("active", True):
            return  # review already completed or cancelled — stale call, ignore
        if state.get("processing"):
            messagebox.showinfo("Busy", "Processing is underway — please wait.")
            return
        review_engine.redo_step(script_dir, state, self.config)

    def _do_cancel(self):
        _logger.info("[dashboard] _do_cancel called")
        state = review_engine.load_state()
        if state and state.get("processing"):
            messagebox.showinfo("Busy", "Processing is underway — cannot cancel right now.")
            return
        if messagebox.askyesno(
            "Cancel Review",
            "Cancel the Evening Review?\nAll progress so far is saved."
        ):
            _logger.info("[dashboard] cancel confirmed by user")
            review_engine.cancel_review(script_dir)
            self.root.destroy()


def main():
    import sys as _sys
    import traceback as _tb_mod

    def _excepthook(exc_type, exc_val, exc_tb):
        msg = "".join(_tb_mod.format_exception(exc_type, exc_val, exc_tb))
        _logger.info(f"[dashboard] UNHANDLED EXCEPTION:\n{msg}")
        _sys.__stderr__.write(f"[dashboard] UNHANDLED EXCEPTION:\n{msg}\n")
    _sys.excepthook = _excepthook

    _logger.info("[dashboard] main() started")
    ctk.set_appearance_mode("dark")
    _logger.info("[dashboard] CTk appearance set")
    root = ctk.CTk()
    _logger.info("[dashboard] CTk window created")

    # GNOME Wayland sends WM_DELETE_WINDOW immediately to background-launched
    # windows (focus-stealing prevention). The default tkinter handler calls
    # root.destroy(), silently killing the window before the user sees it.
    # Suppress it NOW — before any CTk widget creation can process events.
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    _logger.info("[dashboard] WM_DELETE_WINDOW suppressed")

    # lift() is safe on Wayland; focus_force() triggers GNOME focus-stealing
    # defenses and can cause the window to be immediately hidden.
    root.lift()
    root.attributes("-topmost", True)
    root.after(3000, lambda: root.attributes("-topmost", False))

    # Route ALL tkinter callback exceptions to the log file, not just stderr,
    # so crashes inside after() callbacks and widget commands are always visible.
    def _report_tk_error(exc, val, tb):
        _logger.info(
            f"[dashboard] tkinter callback exception: {val}\n"
            + "".join(_tb_mod.format_exception(exc, val, tb))
        )
    root.report_callback_exception = _report_tk_error

    _logger.info("[dashboard] building ReviewDashboard")
    try:
        app = ReviewDashboard(root)
    except Exception as _e:
        _logger.info(
            f"[dashboard] CRASH in ReviewDashboard.__init__: {_e}\n"
            + _tb_mod.format_exc()
        )
        raise
    _logger.info("[dashboard] ReviewDashboard built, entering mainloop")

    def _bind_close():
        root.protocol("WM_DELETE_WINDOW", app._do_cancel)
    root.after(2000, _bind_close)

    def _heartbeat():
        if not app._review_done:
            _logger.info("[dashboard] heartbeat — alive")
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
    _logger.info("[dashboard] mainloop exited")


if __name__ == "__main__":
    main()
