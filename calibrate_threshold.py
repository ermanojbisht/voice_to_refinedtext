#!/usr/bin/env python3
"""Silence Threshold Calibration Utility.

Guides you through 3 rounds of speak → silence → speak → silence,
measures RMS energy at each phase, then recommends the best
SILENCE_THRESHOLD value with a plain-language explanation.

Run:
    python3 calibrate_threshold.py
"""

import threading
import time
import numpy as np
import customtkinter as ctk

SAMPLE_RATE  = 16000
SPEAK_SECS   = 5       # seconds to record while speaking
SILENCE_SECS = 3       # seconds to record while silent
CHUNK        = 1024    # frames per sounddevice read

SENTENCES = [
    "Today I reviewed my work and planned what to do tomorrow.",
    "The morning meeting was productive and we solved the main problem.",
    "I need to focus on completing the project by end of this week.",
]

BG      = "#1e1e2e"
SURFACE = "#313244"
OVERLAY = "#45475a"
TEXT    = "#cdd6f4"
SUBTLE  = "#6c7086"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
YELLOW  = "#f9e2af"


def _rms(audio_float32):
    """RMS in int16 scale (0–32768) — matches SILENCE_THRESHOLD units."""
    return float(np.sqrt(np.mean(audio_float32 ** 2)) * 32768)


def _record(seconds):
    """Record `seconds` of audio and return float32 array."""
    import sounddevice as sd
    frames = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                    channels=1, dtype="float32")
    sd.wait()
    return frames.flatten()


class CalibrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Threshold Calibration")
        self.root.geometry("660x460")
        self.root.configure(fg_color=BG)
        self.root.resizable(False, False)

        self.speech_rms   = []   # one RMS per speak phase
        self.silence_rms  = []   # one RMS per silence phase

        self._build_ui()
        self._start()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        ctk.CTkLabel(self.root, text="🎙 Silence Threshold Calibration",
                     font=("Inter", 18, "bold"), text_color=ACCENT).pack(pady=(20, 4))
        ctk.CTkLabel(self.root, text="Follow the prompts. Keep your mic in its normal position.",
                     font=("Inter", 12), text_color=SUBTLE).pack(pady=(0, 16))

        self.instruction = ctk.CTkLabel(
            self.root, text="", font=("Inter", 14, "bold"),
            text_color=TEXT, wraplength=580, justify="center")
        self.instruction.pack(pady=(0, 8))

        self.sentence_box = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=8)
        self.sentence_box.pack(fill="x", padx=40, pady=(0, 16))
        self.sentence_lbl = ctk.CTkLabel(
            self.sentence_box, text="", font=("Inter", 14),
            text_color=YELLOW, wraplength=540, justify="center")
        self.sentence_lbl.pack(padx=16, pady=12)

        self.progress = ctk.CTkProgressBar(self.root, height=12,
                                           fg_color=OVERLAY, progress_color=ACCENT)
        self.progress.pack(fill="x", padx=40, pady=(0, 6))
        self.progress.set(0)

        self.timer_lbl = ctk.CTkLabel(self.root, text="", font=("Inter", 28, "bold"),
                                      text_color=ACCENT)
        self.timer_lbl.pack(pady=(4, 0))

        self.status_lbl = ctk.CTkLabel(self.root, text="", font=("Inter", 11),
                                       text_color=SUBTLE)
        self.status_lbl.pack(pady=(4, 0))

    def _set(self, instruction="", sentence="", color=TEXT):
        self.instruction.configure(text=instruction, text_color=color)
        self.sentence_lbl.configure(text=sentence)

    def _tick_countdown(self, total):
        """Animate progress bar + timer for `total` seconds (blocking, runs in worker thread)."""
        start = time.time()
        while True:
            elapsed = time.time() - start
            remaining = max(0.0, total - elapsed)
            self.progress.set(elapsed / total)
            self.timer_lbl.configure(text=f"{remaining:.1f}s")
            if elapsed >= total:
                break
            time.sleep(0.05)
        self.progress.set(1.0)
        self.timer_lbl.configure(text="")

    def _get_ready_countdown(self, seconds=3):
        """Show a 'Get ready' beep-style countdown — no recording, just preparation time."""
        self.progress.set(0)
        for remaining in range(seconds, 0, -1):
            self.timer_lbl.configure(text=str(remaining), text_color=YELLOW)
            time.sleep(1)
        self.timer_lbl.configure(text="NOW →", text_color=GREEN)
        time.sleep(0.4)
        self.timer_lbl.configure(text="")

    # ── Calibration flow ──────────────────────────────────────────────────────

    def _start(self):
        """Show welcome screen with a Start button — user decides when they are ready."""
        # Replace sentence box content with welcome text
        self._set(
            instruction="This utility records your voice and silence to find\nthe best Silence Threshold for your microphone.",
            sentence="Make sure your microphone is connected and positioned\nas you normally use it. Click Start when ready.",
            color=ACCENT)
        self.status_lbl.configure(text="3 rounds of: read a sentence → stay silent")
        self.timer_lbl.configure(text="")
        self.progress.set(0)

        self.start_btn = ctk.CTkButton(
            self.root, text="▶  Start Calibration",
            font=("Inter", 14, "bold"), fg_color=ACCENT, text_color=BG,
            height=40, command=self._on_start_clicked)
        self.start_btn.pack(pady=12)

    def _on_start_clicked(self):
        self.start_btn.destroy()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            import sounddevice  # noqa — fail fast if not installed
        except ImportError:
            self._set("❌ sounddevice not installed.\nRun: pip install sounddevice", color=RED)
            return

        total = len(SENTENCES)

        for i, sentence in enumerate(SENTENCES):
            round_num = i + 1

            # ── Prepare for speak phase ───────────────────────────────────────
            self._set(
                instruction=f"Round {round_num} of {total}  —  Get ready to READ this sentence aloud:",
                sentence=sentence,
                color=ACCENT)
            self.status_lbl.configure(text="Read it clearly in your normal speaking voice.")
            self._get_ready_countdown(seconds=4)

            # ── Speak phase ───────────────────────────────────────────────────
            self._set(
                instruction=f"Round {round_num} of {total}  —  SPEAK NOW:  🎙",
                sentence=sentence,
                color=GREEN)
            self.status_lbl.configure(text="Recording your voice…")
            audio_speak = self._record_with_countdown(SPEAK_SECS)
            rms_speak   = _rms(audio_speak)
            self.speech_rms.append(rms_speak)

            # ── Rest between phases ───────────────────────────────────────────
            self._set(
                instruction=f"Round {round_num} of {total}  —  Good! Next: SILENCE.",
                sentence="Prepare to stay completely quiet — no talking, no movement.",
                color=ACCENT)
            self.status_lbl.configure(text=f"Your voice RMS just now: {rms_speak:.0f}")
            self._get_ready_countdown(seconds=3)

            # ── Silence phase ─────────────────────────────────────────────────
            self._set(
                instruction=f"Round {round_num} of {total}  —  STAY SILENT NOW  🤫",
                sentence="Do not speak. Breathe normally. Hold still.",
                color=YELLOW)
            self.status_lbl.configure(text="Recording silence…")
            audio_silence = self._record_with_countdown(SILENCE_SECS)
            rms_silence   = _rms(audio_silence)
            self.silence_rms.append(rms_silence)

            # ── Between rounds ────────────────────────────────────────────────
            if round_num < total:
                self._set(
                    instruction=f"Round {round_num} done.  Next round coming up…",
                    sentence="",
                    color=SUBTLE)
                self.status_lbl.configure(
                    text=f"Silence RMS: {rms_silence:.0f}  |  Relax for a moment.")
                time.sleep(2.5)

        self._show_report()

    def _record_with_countdown(self, seconds):
        """Start recording in background; animate countdown in foreground."""
        result = [None]

        def _worker():
            result[0] = _record(seconds)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        self._tick_countdown(seconds)
        t.join()
        return result[0]

    # ── Report ────────────────────────────────────────────────────────────────

    def _show_report(self):
        speech_min  = min(self.speech_rms)
        speech_max  = max(self.speech_rms)
        speech_avg  = sum(self.speech_rms) / len(self.speech_rms)
        silence_min = min(self.silence_rms)
        silence_max = max(self.silence_rms)
        silence_avg = sum(self.silence_rms) / len(self.silence_rms)

        # Clear current UI
        for w in self.root.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.root, text="📊 Calibration Report",
                     font=("Inter", 18, "bold"), text_color=ACCENT).pack(pady=(20, 8))

        # Numbers table
        tbl = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=8)
        tbl.pack(fill="x", padx=30, pady=(0, 12))

        def row(label, val, color=TEXT):
            f = ctk.CTkFrame(tbl, fg_color="transparent")
            f.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(f, text=label, font=("Inter", 12), text_color=SUBTLE,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=str(val), font=("Inter", 12, "bold"),
                         text_color=color, anchor="e").pack(side="right")

        row("Your voice  — min / avg / max RMS",
            f"{speech_min:.0f} / {speech_avg:.0f} / {speech_max:.0f}", GREEN)
        row("Silence     — min / avg / max RMS",
            f"{silence_min:.0f} / {silence_avg:.0f} / {silence_max:.0f}", YELLOW)

        # Compute recommendation
        gap = speech_min - silence_max

        if gap > 50:
            # Clear separation — place threshold at silence_max + 40% of gap
            suggested = int(silence_max + gap * 0.40)
            confidence = "High confidence"
            conf_color = GREEN
            reason = (
                f"Your voice ({speech_min:.0f}–{speech_max:.0f}) is clearly louder than "
                f"background silence ({silence_min:.0f}–{silence_max:.0f}). "
                f"The gap between them is {gap:.0f} units. "
                f"Setting the threshold at {suggested} sits 40% into that gap — "
                f"high enough to ignore silence/background noise, low enough to never "
                f"miss your voice."
            )
        elif gap > 0:
            # Small but positive gap — be conservative
            suggested = int(silence_max + gap * 0.25)
            confidence = "Moderate confidence"
            conf_color = YELLOW
            reason = (
                f"Your voice ({speech_min:.0f}–{speech_max:.0f}) is slightly louder than "
                f"silence ({silence_min:.0f}–{silence_max:.0f}), but the gap is only "
                f"{gap:.0f} units — narrow. "
                f"Threshold set conservatively at {suggested} (25% into the gap). "
                f"If recording cuts off too early, lower it by 20–30. "
                f"Consider recording in a quieter environment for a cleaner reading."
            )
        else:
            # Overlap — problematic
            suggested = int(silence_avg * 1.5)
            confidence = "Low confidence — voice/silence overlap"
            conf_color = RED
            reason = (
                f"Your silence RMS ({silence_max:.0f}) is as loud as or louder than your "
                f"softest speech ({speech_min:.0f}). This usually means high background "
                f"noise (fan, AC, traffic). The suggested value of {suggested} is a rough "
                f"midpoint but may not work reliably. Try: move closer to the mic, "
                f"reduce background noise, or use a directional microphone."
            )

        row("Suggested SILENCE_THRESHOLD", suggested, ACCENT)
        row("Confidence", confidence, conf_color)

        # Reason box
        reason_frame = ctk.CTkFrame(self.root, fg_color=OVERLAY, corner_radius=8)
        reason_frame.pack(fill="x", padx=30, pady=(0, 12))
        ctk.CTkLabel(reason_frame, text="Why this value?",
                     font=("Inter", 11, "bold"), text_color=ACCENT).pack(
                     anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(reason_frame, text=reason, font=("Inter", 11),
                     text_color=TEXT, wraplength=560, justify="left").pack(
                     padx=12, pady=(0, 10))

        # Apply button
        btn_row = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_row.pack(pady=(4, 0))
        ctk.CTkButton(btn_row, text=f"Apply {suggested} to config.json",
                      font=("Inter", 13, "bold"), fg_color=ACCENT, text_color=BG,
                      command=lambda: self._apply(suggested)).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Close", font=("Inter", 13),
                      fg_color=OVERLAY, text_color=TEXT,
                      command=self.root.destroy).pack(side="left", padx=8)

    def _apply(self, value):
        import json, os
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["SILENCE_THRESHOLD"] = value
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            # Feedback
            for w in self.root.winfo_children():
                if isinstance(w, ctk.CTkFrame):
                    for btn in w.winfo_children():
                        if hasattr(btn, "configure") and "Apply" in str(getattr(btn, "_text", "")):
                            btn.configure(text=f"✓ Applied {value}", state="disabled",
                                          fg_color=GREEN, text_color=BG)
        except Exception as e:
            ctk.CTkLabel(self.root, text=f"Error saving: {e}",
                         text_color=RED, font=("Inter", 11)).pack()


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    CalibrationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
