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
from tkinter import ttk, messagebox

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import review_engine

# Route dashboard logs to the project log file (not stdout)
review_engine.init_logging(script_dir)

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
        self.root = root
        self.root.title("Evening Review")
        self.root.geometry("500x580")
        self.root.configure(bg=BG)
        self.root.resizable(False, True)

        self.config = review_engine.load_review_config(script_dir)
        self.steps  = self.config.get("review_steps", [])
        self.is_processing = False
        self._review_done  = False   # set True once complete; stops polling
        self._engine = None          # lazy — only loaded when Next Step is clicked

        self._build_ui()
        self._poll_state()

    # ── Engine (lazy, for LLM structuring only) ────────────────────────────────

    @property
    def engine(self):
        if self._engine is None:
            from engine import VoiceEngine
            self._engine = VoiceEngine(script_dir)
        return self._engine

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header bar
        hdr = tk.Frame(self.root, bg=ACCENT, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🌙  Evening Review", bg=ACCENT, fg=BG,
                 font=("Sans", 14, "bold")).pack(side=tk.LEFT, padx=16)
        tk.Label(hdr, text="powered by AI Voice Refiner", bg=ACCENT, fg=BG,
                 font=("Sans", 9)).pack(side=tk.RIGHT, padx=16)

        # Subtitle (current step description)
        self.subtitle_var = tk.StringVar(value="Initialising…")
        tk.Label(self.root, textvariable=self.subtitle_var, bg=BG, fg=TEXT,
                 font=("Sans", 11), anchor="w").pack(fill=tk.X, padx=20, pady=(10, 2))

        # Progress bar
        prog_frame = tk.Frame(self.root, bg=BG)
        prog_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.prog_canvas = tk.Canvas(prog_frame, height=8, bg=OVERLAY,
                                     highlightthickness=0)
        self.prog_canvas.pack(fill=tk.X)
        self.prog_rect = self.prog_canvas.create_rectangle(0, 0, 0, 8,
                                                            fill=GREEN, width=0)

        # Steps list
        steps_frame = tk.Frame(self.root, bg=BG)
        steps_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        self.row_frames    = []
        self.icon_labels   = []
        self.name_labels   = []
        self.status_labels = []

        for step in self.steps:
            row = tk.Frame(steps_frame, bg=SURFACE, pady=9, padx=12)
            row.pack(fill=tk.X, pady=3)

            # Plain font — emoji glyphs render via the OS on Linux
            icon_lbl = tk.Label(row, text="○", bg=SURFACE, fg=SUBTLE,
                                font=("Sans", 14), width=3, anchor="center")
            icon_lbl.pack(side=tk.LEFT)

            name_lbl = tk.Label(row, text=step["section_name"], bg=SURFACE,
                                fg=SUBTLE, font=("Sans", 11, "bold"), anchor="w")
            name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            status_lbl = tk.Label(row, text="Pending", bg=SURFACE,
                                  fg=SUBTLE, font=("Sans", 10), width=16, anchor="e")
            status_lbl.pack(side=tk.RIGHT)

            self.row_frames.append(row)
            self.icon_labels.append(icon_lbl)
            self.name_labels.append(name_lbl)
            self.status_labels.append(status_lbl)

        # Divider
        tk.Frame(self.root, bg=OVERLAY, height=1).pack(fill=tk.X, padx=20, pady=8)

        # Primary buttons (Record + Next Step)
        btn_row1 = tk.Frame(self.root, bg=BG)
        btn_row1.pack(fill=tk.X, padx=20, pady=(0, 6))

        self.record_btn = tk.Button(
            btn_row1, text="🎤  Record", command=self._do_record,
            bg=ACCENT, fg=BG, font=("Sans", 12, "bold"),
            relief=tk.FLAT, padx=18, pady=9, cursor="hand2", bd=0
        )
        self.record_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.next_btn = tk.Button(
            btn_row1, text="▶  Next Step", command=self._do_next,
            bg=GREEN, fg=BG, font=("Sans", 12, "bold"),
            relief=tk.FLAT, padx=18, pady=9, cursor="hand2", bd=0,
            state=tk.DISABLED
        )
        self.next_btn.pack(side=tk.LEFT)

        # Secondary buttons (Skip, Redo, Cancel)
        btn_row2 = tk.Frame(self.root, bg=BG)
        btn_row2.pack(fill=tk.X, padx=20, pady=(0, 14))

        self.skip_btn = tk.Button(
            btn_row2, text="⏭  Skip", command=self._do_skip,
            bg=OVERLAY, fg=TEXT, font=("Sans", 11),
            relief=tk.FLAT, padx=12, pady=6, cursor="hand2", bd=0
        )
        self.skip_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.redo_btn = tk.Button(
            btn_row2, text="↩  Redo", command=self._do_redo,
            bg=OVERLAY, fg=TEXT, font=("Sans", 11),
            relief=tk.FLAT, padx=12, pady=6, cursor="hand2", bd=0
        )
        self.redo_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.cancel_btn = tk.Button(
            btn_row2, text="✕  Cancel Review", command=self._do_cancel,
            bg=RED, fg=BG, font=("Sans", 11, "bold"),
            relief=tk.FLAT, padx=12, pady=6, cursor="hand2", bd=0
        )
        self.cancel_btn.pack(side=tk.RIGHT)

    # ── Live polling ───────────────────────────────────────────────────────────

    def _poll_state(self):
        # Stop polling once the review is done to avoid 500ms timer spam
        if self._review_done:
            return

        try:
            active, state = review_engine.is_review_active(script_dir)
            if active and state:
                self._update_ui(state)
            else:
                # Only show complete if the state file is truly gone
                raw_state = review_engine._load_state()
                if raw_state is None:
                    self._show_complete()
                    return  # _show_complete sets _review_done; don't reschedule
        except Exception:
            pass

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
        self.root.update_idletasks()
        w = self.prog_canvas.winfo_width() or 460
        filled = int(w * idx / total) if total else 0
        self.prog_canvas.coords(self.prog_rect, 0, 0, filled, 8)

        # Step rows
        for i in range(len(self.steps)):
            frame    = self.row_frames[i]
            icon_lbl = self.icon_labels[i]
            name_lbl = self.name_labels[i]
            st_lbl   = self.status_labels[i]

            if i < idx:
                icon_lbl.config(text="✅", fg=GREEN, bg=SURFACE)
                name_lbl.config(fg=SUBTLE, bg=SURFACE)
                st_lbl.config(text="Saved", fg=GREEN, bg=SURFACE)
                frame.config(bg=SURFACE)

            elif i == idx:
                frame.config(bg=OVERLAY)
                icon_lbl.config(bg=OVERLAY)
                name_lbl.config(bg=OVERLAY, fg=TEXT)
                st_lbl.config(bg=OVERLAY)

                if busy:
                    icon_lbl.config(text="⏳", fg=YELLOW)
                    st_lbl.config(text="Processing…", fg=YELLOW)
                elif awaiting:
                    icon_lbl.config(text="✓", fg=ACCENT)
                    st_lbl.config(text=f"{clips} clip{'s' if clips != 1 else ''} · ready", fg=ACCENT)
                else:
                    icon_lbl.config(text="🎤", fg=RED)
                    st_lbl.config(text="Speak now", fg=RED)

            else:
                icon_lbl.config(text="○", fg=SUBTLE, bg=SURFACE)
                name_lbl.config(fg=SUBTLE, bg=SURFACE)
                st_lbl.config(text="Pending", fg=SUBTLE, bg=SURFACE)
                frame.config(bg=SURFACE)

        # Button states
        self.record_btn.config(
            state=tk.DISABLED if busy else tk.NORMAL,
            text="⏳  Processing…" if busy else "🎤  Record",
            bg=OVERLAY if busy else ACCENT
        )
        self.next_btn.config(state=tk.NORMAL if (awaiting and not busy) else tk.DISABLED)
        self.skip_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
        self.redo_btn.config(state=tk.DISABLED if busy else tk.NORMAL)

    def _show_complete(self):
        self._review_done = True  # stop the polling loop
        self.subtitle_var.set("✅  Evening Review complete!")
        for i in range(len(self.steps)):
            self.icon_labels[i].config(text="✅", fg=GREEN, bg=SURFACE)
            self.name_labels[i].config(fg=SUBTLE, bg=SURFACE)
            self.status_labels[i].config(text="Done", fg=GREEN, bg=SURFACE)
            self.row_frames[i].config(bg=SURFACE)
        self.prog_canvas.coords(self.prog_rect, 0, 0, 9999, 8)
        for btn in (self.record_btn, self.next_btn, self.skip_btn, self.redo_btn):
            btn.config(state=tk.DISABLED)
        self.cancel_btn.config(
            text="Close", bg=OVERLAY, fg=TEXT,
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
        state = review_engine._load_state()
        if state and state.get("processing"):
            messagebox.showinfo("Busy", "Processing is underway — cannot cancel right now.")
            return
        if messagebox.askyesno(
            "Cancel Review",
            "Cancel the Evening Review?\nAll progress so far is saved."
        ):
            review_engine.cancel_review(script_dir)
            self.root.destroy()


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    app = ReviewDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
