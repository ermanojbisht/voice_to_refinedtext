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
        self.root = root
        self.root.title("Evening Review")
        self.root.geometry("550x620")
        self.root.configure(fg_color=BG)
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
        hdr = ctk.CTkFrame(self.root, fg_color=ACCENT, corner_radius=0, height=50)
        hdr.pack(fill=ctk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🌙 Evening Review", text_color=BG,
                     font=("Inter", 18, "bold")).pack(side=ctk.LEFT, padx=20)
        ctk.CTkLabel(hdr, text="powered by AI Voice Refiner", text_color=BG,
                     font=("Inter", 12)).pack(side=ctk.RIGHT, padx=20)

        # Subtitle (current step description)
        self.subtitle_var = ctk.StringVar(value="Initialising…")
        ctk.CTkLabel(self.root, textvariable=self.subtitle_var, fg_color="transparent", text_color=TEXT,
                     font=("Inter", 14), anchor="w").pack(fill=ctk.X, padx=24, pady=(20, 5))

        # Progress bar
        self.prog_canvas = ctk.CTkProgressBar(self.root, height=8, fg_color=OVERLAY,
                                     progress_color=GREEN, corner_radius=4)
        self.prog_canvas.pack(fill=ctk.X, padx=24, pady=(0, 15))
        self.prog_canvas.set(0)

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

        # Primary buttons (Record + Next Step)
        btn_row1 = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_row1.pack(fill=ctk.X, padx=24, pady=(15, 8))

        self.record_btn = ctk.CTkButton(
            btn_row1, text="🎤 Record", command=self._do_record,
            fg_color=ACCENT, text_color=BG, font=("Inter", 14, "bold"),
            hover_color="#b4befe", corner_radius=8, height=40
        )
        self.record_btn.pack(side=ctk.LEFT, expand=True, fill=ctk.X, padx=(0, 8))

        self.next_btn = ctk.CTkButton(
            btn_row1, text="▶ Next Step", command=self._do_next,
            fg_color=GREEN, text_color=BG, font=("Inter", 14, "bold"),
            hover_color="#89dceb", corner_radius=8, height=40, state="disabled"
        )
        self.next_btn.pack(side=ctk.LEFT, expand=True, fill=ctk.X)

        # Secondary buttons (Skip, Redo, Cancel)
        btn_row2 = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_row2.pack(fill=ctk.X, padx=24, pady=(0, 20))

        self.skip_btn = ctk.CTkButton(
            btn_row2, text="⏭ Skip", command=self._do_skip,
            fg_color=OVERLAY, text_color=TEXT, font=("Inter", 12),
            hover_color=SURFACE, corner_radius=6, height=32, width=80
        )
        self.skip_btn.pack(side=ctk.LEFT, padx=(0, 8))

        self.redo_btn = ctk.CTkButton(
            btn_row2, text="↩ Redo", command=self._do_redo,
            fg_color=OVERLAY, text_color=TEXT, font=("Inter", 12),
            hover_color=SURFACE, corner_radius=6, height=32, width=80
        )
        self.redo_btn.pack(side=ctk.LEFT, padx=(0, 8))

        self.cancel_btn = ctk.CTkButton(
            btn_row2, text="✕ Cancel", command=self._do_cancel,
            fg_color=RED, text_color=BG, font=("Inter", 12, "bold"),
            hover_color="#f5c2e7", corner_radius=6, height=32, width=80
        )
        self.cancel_btn.pack(side=ctk.RIGHT)

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
                raw_state = review_engine._load_state()
                if raw_state is None:
                    # State file gone — review completed normally
                    self._show_complete()
                    return
                # State file exists but review is no longer active (expired or
                # active=False). Either way the session is over for the dashboard.
                if not raw_state.get("active", True):
                    self._show_complete()
                    return
                # Check expiry ourselves to avoid the dashboard freezing on "Initialising…"
                try:
                    import datetime
                    started = datetime.datetime.fromisoformat(raw_state["started_at"])
                    expiry_h = self.config.get("review_expiry_hours", 1)
                    if (datetime.datetime.now() - started).total_seconds() / 3600 > expiry_h:
                        self._show_complete()
                        return
                except Exception:
                    pass
                # Transient false return — keep polling
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

        # Button states
        self.record_btn.configure(
            state="disabled" if busy else "normal",
            text="⏳ Processing…" if busy else "🎤 Record",
            fg_color=OVERLAY if busy else ACCENT
        )
        self.next_btn.configure(state="normal" if (awaiting and not busy) else "disabled")
        self.skip_btn.configure(state="disabled" if busy else "normal")
        self.redo_btn.configure(state="disabled" if busy else "normal")

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
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()

    # Bring window to front so it's not hidden behind other windows
    root.lift()
    root.attributes("-topmost", True)
    root.after(2000, lambda: root.attributes("-topmost", False))
    try:
        root.focus_force()
    except Exception:
        pass

    app = ReviewDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
