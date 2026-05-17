#!/usr/bin/env python3
"""Evening Review Dashboard — live status panel for the review session.

Opens automatically when a review starts (launched by tray_app.py).
Polls /tmp/review_state.json every 500 ms to stay in sync with the tray.
Buttons communicate with the tray via SIGUSR1 (record) or call review_engine
directly (skip / redo / cancel / next-step structuring).
"""
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
        self.root.geometry("690x925")
        self.root.minsize(600, 700)
        review_engine._rlog("[dashboard] geometry set")
        self.root.configure(fg_color=BG)
        review_engine._rlog("[dashboard] fg_color configured")
        self.root.resizable(True, True)
        review_engine._rlog("[dashboard] resizable set")

        self.config = review_engine.load_review_config(script_dir)
        review_engine._rlog("[dashboard] config loaded")
        self.steps  = self.config.get("review_steps", [])
        self.is_processing = False
        self._review_done  = False
        self._last_context_step = -1
        self._engine = None

        review_engine._rlog("[dashboard] calling _build_ui")
        self._build_ui()
        review_engine._rlog("[dashboard] _build_ui done, scheduling first poll")
        # Schedule _poll_state via after() so it runs INSIDE mainloop, not before.
        # Calling it synchronously before mainloop causes CTkButton.configure() to
        # run before Tcl/Tk is ready, silently crashing the process.
        self.root.after(200, self._poll_state)
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
        # Header bar
        hdr = ctk.CTkFrame(self.root, fg_color=ACCENT, corner_radius=0, height=50)
        hdr.pack(fill=ctk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🌙 Evening Review", text_color=BG,
                     font=("Inter", 18, "bold")).pack(side=ctk.LEFT, padx=20)
        ctk.CTkLabel(hdr, text="powered by AI Voice Refiner", text_color=BG,
                     font=("Inter", 12)).pack(side=ctk.RIGHT, padx=20)

        review_engine._rlog("[dashboard] _build_ui: subtitle")
        # Subtitle (current step description)
        self.subtitle_var = ctk.StringVar(value="Initialising…")
        ctk.CTkLabel(self.root, textvariable=self.subtitle_var, fg_color="transparent", text_color=TEXT,
                     font=("Inter", 14), anchor="w").pack(fill=ctk.X, padx=24, pady=(20, 5))

        review_engine._rlog("[dashboard] _build_ui: progress bar")
        # Progress bar
        self.prog_canvas = ctk.CTkProgressBar(self.root, height=8, fg_color=OVERLAY,
                                     progress_color=GREEN, corner_radius=4)
        self.prog_canvas.pack(fill=ctk.X, padx=24, pady=(0, 15))
        self.prog_canvas.set(0)

        review_engine._rlog("[dashboard] _build_ui: context panel")
        # Context panel (last N days brief)
        ctx_outer = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=8)
        ctx_outer.pack(fill=ctk.X, padx=16, pady=(0, 10))

        ctx_hdr = ctk.CTkFrame(ctx_outer, fg_color="transparent")
        ctx_hdr.pack(fill=ctk.X, padx=10, pady=(6, 0))
        ctk.CTkLabel(ctx_hdr, text="📅 Context", text_color=ACCENT,
                     font=("Inter", 11, "bold")).pack(side=ctk.LEFT)
        self.ctx_days_lbl = ctk.CTkLabel(ctx_hdr, text="", text_color=SUBTLE,
                                          font=("Inter", 10))
        self.ctx_days_lbl.pack(side=ctk.RIGHT)

        review_engine._rlog("[dashboard] _build_ui: ctx_text (CTkTextbox)")
        self.ctx_text = ctk.CTkTextbox(ctx_outer, height=160, fg_color="transparent",
                                        text_color=SUBTLE, font=("Inter", 11),
                                        wrap="word", activate_scrollbars=True)
        review_engine._rlog("[dashboard] _build_ui: ctx_text created, packing")
        self.ctx_text.pack(fill=ctk.X, padx=10, pady=(2, 8))
        review_engine._rlog("[dashboard] _build_ui: ctx_text insert")
        self.ctx_text.insert("end", "Analysing last days…")
        review_engine._rlog("[dashboard] _build_ui: ctx_text disable")
        self.ctx_text.configure(state="disabled")

        review_engine._rlog("[dashboard] _build_ui: CTkScrollableFrame")
        # Steps list
        steps_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        steps_frame.pack(fill=ctk.BOTH, expand=True, padx=16)

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
            btn_row1 = ctk.CTkFrame(self.root, fg_color="transparent")
            btn_row1.pack(fill=ctk.X, padx=24, pady=(15, 8))

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
            btn_row2 = ctk.CTkFrame(self.root, fg_color="transparent")
            btn_row2.pack(fill=ctk.X, padx=24, pady=(0, 20))

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

    # ── Live polling ───────────────────────────────────────────────────────────

    def _poll_state(self):
        # Stop polling once the review is done to avoid 500ms timer spam
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
                    # State file gone — review completed normally
                    review_engine._rlog("[dashboard] _poll_state: state gone → showing complete")
                    self._show_complete()
                    return
                # State file exists but review is no longer active (expired or
                # active=False). Either way the session is over for the dashboard.
                if not raw_state.get("active", True):
                    review_engine._rlog("[dashboard] _poll_state: active=False → showing complete")
                    self._show_complete()
                    return
                # Check expiry ourselves to avoid the dashboard freezing on "Initialising…"
                try:
                    import datetime
                    started = datetime.datetime.fromisoformat(raw_state["started_at"])
                    expiry_h = self.config.get("review_expiry_hours", 1)
                    if (datetime.datetime.now() - started).total_seconds() / 3600 > expiry_h:
                        review_engine._rlog("[dashboard] _poll_state: expired → showing complete")
                        self._show_complete()
                        return
                except Exception:
                    pass
                # Transient false return — keep polling
        except Exception as e:
            import traceback
            review_engine._rlog(f"[dashboard] _poll_state exception: {traceback.format_exc()}")

        self.root.after(500, self._poll_state)

    def _update_ui(self, state):
        idx      = state.get("current_step_index", 0)
        total    = len(self.steps)
        awaiting = state.get("awaiting_more", False)
        clips    = len(state.get("accumulated_raw", []))
        # Treat "processing" flag in state as busy (set by tray or dashboard)
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
        filled = idx / total if total else 0
        self.prog_canvas.set(filled)

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

        # Context panel
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

    def _update_context_panel(self, state):
        """Refresh the context panel from state. Called from _update_ui."""
        n = self.config.get("last_n_days_context", 3)
        per_step = self.config.get("per_step_context", False)
        idx = state.get("current_step_index", 0)
        notes_data = state.get("context_notes", [])

        if not state.get("context_ready"):
            # Still loading
            self.ctx_days_lbl.configure(text=f"last {n} days")
            self._set_ctx_text("Analysing last days…", SUBTLE)
            return

        if per_step and notes_data and idx < len(self.steps):
            # Per-step: show only the relevant section from past notes
            section_name = self.steps[idx]["section_name"]
            if idx != self._last_context_step:
                self._last_context_step = idx
                lines = []
                for note in reversed(notes_data):
                    snippet = review_engine._extract_step_section(section_name, note["content"])
                    if snippet:
                        lines.append(f"{note['date']}: {snippet}")
                if lines:
                    text = "\n".join(lines)
                    label = f"{section_name} · last {len(notes_data)} day(s)"
                else:
                    text = f"No {section_name} entries found in last {len(notes_data)} day(s)."
                    label = f"last {len(notes_data)} day(s)"
                self.ctx_days_lbl.configure(text=label)
                self._set_ctx_text(text, TEXT)
        else:
            # Global brief (show once, don't repeat on step change)
            if self._last_context_step == -1:
                self._last_context_step = 0
                brief = state.get("context_brief", "")
                found = len(notes_data)
                label = f"last {found} day(s)" if found else f"last {n} days"
                self.ctx_days_lbl.configure(text=label)
                self._set_ctx_text(brief or "No context available.", TEXT if brief else SUBTLE)

    def _set_ctx_text(self, text, color):
        self.ctx_text.configure(state="normal")
        self.ctx_text.delete("1.0", "end")
        self.ctx_text.insert("end", text)
        self.ctx_text.configure(state="disabled", text_color=color)

    def _show_complete(self):
        self._review_done = True  # stop the polling loop
        self.subtitle_var.set("✅ Evening Review complete!")
        for i in range(len(self.steps)):
            self.icon_labels[i].configure(text="✅", text_color=GREEN)
            self.name_labels[i].configure(text_color=SUBTLE)
            self.status_labels[i].configure(text="Done", text_color=GREEN)
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
        # Re-read freshest state from disk
        state = review_engine._load_state()
        if state is None:
            return
        # Honour the processing lock set by either tray or this dashboard
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
            # Re-read once more inside the thread for the absolute freshest state
            fresh_state = review_engine._load_state()
            if fresh_state is None:
                return
            if fresh_state.get("processing"):
                # Tray grabbed the lock first — bail without touching anything
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
            # Only release the lock if WE set it
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

    # Catch any unhandled Python exception (including ones not printed to stderr)
    # and write them to the log so crashes are always visible.
    def _excepthook(exc_type, exc_val, exc_tb):
        msg = "".join(_tb_mod.format_exception(exc_type, exc_val, exc_tb))
        review_engine._rlog(f"[dashboard] UNHANDLED EXCEPTION:\n{msg}")
        # Also write to stderr so it appears in the subprocess log_fh
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

    # Bring window to front — lift() is safe; focus_force() can trigger
    # GNOME focus-stealing defenses on Wayland, so we skip it.
    root.lift()
    root.attributes("-topmost", True)
    root.after(3000, lambda: root.attributes("-topmost", False))

    # Override tkinter's exception reporter so ALL callback errors go to log
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

    # Now that the window is fully built, route close to the cancel dialog
    def _bind_close():
        root.protocol("WM_DELETE_WINDOW", app._do_cancel)

    root.after(2000, _bind_close)

    # Heartbeat: log every 5 s so we can confirm the dashboard is alive
    def _heartbeat():
        if not app._review_done:
            review_engine._rlog("[dashboard] heartbeat — alive")
            root.after(5000, _heartbeat)

    root.after(5000, _heartbeat)

    # Wayland: wmctrl can raise XWayland windows to the foreground
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
