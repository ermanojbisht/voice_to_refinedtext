#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import queue
import os
import subprocess
import time
import sys
import numpy as np
from engine import VoiceEngine
from theme import (
    BG, SURFACE, OVERLAY, FIELD, BORDER, TEXT, SUBTLE, MUTED,
    ACCENT, PRIMARY, PRIMARY_HOVER, GREEN, RED, YELLOW
)

# Colors backwards compatibility
BG_COLOR = BG
TEXT_COLOR = TEXT
ACCENT_COLOR = ACCENT
RECORD_COLOR = RED
SUCCESS_COLOR = GREEN

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Refiner")
        self.root.geometry("640x780")
        self.root.minsize(580, 680)
        self.root.configure(fg_color=BG)
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.engine = VoiceEngine(self.script_dir)
        
        # Internal State
        self.is_recording = False
        self.status_queue = queue.Queue()
        
        self.setup_ui()
        self.check_queue()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=24, pady=20)

        # ── Header & Badges ──────────────────────────────────────────
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill=ctk.X, pady=(0, 16))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side=ctk.LEFT)
        ctk.CTkLabel(title_box, text="🎙 AI Voice Refiner", font=("Inter", 18, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Instant local speech transcription & AI refinement", font=("Inter", 11), text_color=MUTED).pack(anchor="w")

        # Status Badges
        badges_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        badges_box.pack(side=ctk.RIGHT, pady=2)

        active_prof = self.engine.config.get("ACTIVE_MODEL_PROFILE", "default")
        lang_mode = self.engine.config.get("LANGUAGE_MODE", "bilingual")
        mode_labels = {
            "bilingual": "🔀 Bilingual",
            "pure_english": "🇬🇧 Pure English",
            "pure_hindi": "🇮🇳 Pure Hindi",
            "roman_hinglish": "💬 Roman Hinglish",
        }
        
        self.profile_badge = ctk.CTkLabel(
            badges_box, text=f"⚡ {active_prof}", font=("Inter", 10, "bold"),
            fg_color=SURFACE, text_color=ACCENT, corner_radius=6, padx=8, pady=3
        )
        self.profile_badge.pack(side=ctk.RIGHT, padx=(4, 0))

        self.mode_badge = ctk.CTkLabel(
            badges_box, text=mode_labels.get(lang_mode, f"🌐 {lang_mode.title()}"),
            font=("Inter", 10, "bold"), fg_color=SURFACE, text_color=SUBTLE, corner_radius=6, padx=8, pady=3
        )
        self.mode_badge.pack(side=ctk.RIGHT, padx=(4, 0))

        self.btn_manual = ctk.CTkButton(
            badges_box, text="📖 Manual", font=("Inter", 10, "bold"),
            fg_color=SURFACE, hover_color=OVERLAY, text_color=ACCENT,
            corner_radius=6, width=70, height=24,
            command=self.open_manual
        )
        self.btn_manual.pack(side=ctk.RIGHT, padx=(4, 0))

        # ── Recording Hero Card ──────────────────────────────────────
        self.record_card = ctk.CTkFrame(
            main_frame, fg_color=SURFACE, corner_radius=16,
            border_width=1, border_color=BORDER
        )
        self.record_card.pack(fill=ctk.X, pady=(0, 16), padx=2)

        self.status_label = ctk.CTkLabel(
            self.record_card, text="Ready to Record", text_color=TEXT, font=("Inter", 15, "bold")
        )
        self.status_label.pack(pady=(18, 4))

        self.sub_status_label = ctk.CTkLabel(
            self.record_card, text="Click Start Recording or press your global hotkey",
            text_color=MUTED, font=("Inter", 11)
        )
        self.sub_status_label.pack(pady=(0, 6))

        # Next-Level Animated Visualizer Canvas (Ear 👂 / Brain 🧠 / Mic 🎙)
        self.canvas = tk.Canvas(self.record_card, width=140, height=140, bg=SURFACE, highlightthickness=0)
        self.canvas.pack(pady=8)
        
        # Canvas elements
        self.glow_ring = self.canvas.create_oval(14, 14, 126, 126, outline=OVERLAY, width=1.5)
        self.indicator = self.canvas.create_oval(32, 32, 108, 108, fill=FIELD, outline=BORDER, width=2)
        
        # Acoustic soundwave arcs for listening state
        self.soundwave_arcs = [
            self.canvas.create_arc(22, 22, 118, 118, start=-50, extent=100, style="arc", width=2.5, outline=RECORD_COLOR, state="hidden"),
            self.canvas.create_arc(14, 14, 126, 126, start=-55, extent=110, style="arc", width=2.0, outline=RECORD_COLOR, state="hidden"),
            self.canvas.create_arc(6, 6, 134, 134, start=-60, extent=120, style="arc", width=1.5, outline=RECORD_COLOR, state="hidden"),
        ]
        
        # Synaptic orbit and sparks for thinking state
        self.orbit_ring = self.canvas.create_oval(14, 38, 126, 102, outline=OVERLAY, width=1, state="hidden")
        self.spark_nodes = [
            self.canvas.create_oval(0, 0, 8, 8, fill=YELLOW, outline="", state="hidden"),
            self.canvas.create_oval(0, 0, 8, 8, fill=ACCENT_COLOR, outline="", state="hidden"),
            self.canvas.create_oval(0, 0, 8, 8, fill=ACCENT_COLOR, outline="", state="hidden"),
        ]
        
        # Center expressive glyph
        self.center_glyph = self.canvas.create_text(70, 70, text="🎙", font=("Inter", 26))

        self.visual_state = "idle"
        self.anim_start_time = time.time()
        self.anim_loop_id = None

        self.action_btn = ctk.CTkButton(
            self.record_card, text="Start Recording", 
            command=self.toggle_recording,
            fg_color=ACCENT, text_color=BG,
            font=("Inter", 14, "bold"), hover_color=PRIMARY_HOVER,
            corner_radius=10, height=44, width=220
        )
        self.action_btn.pack(pady=(10, 16))

        self.progress = ctk.CTkProgressBar(
            self.record_card, width=320, mode='indeterminate',
            progress_color=ACCENT, border_color=BORDER, fg_color=FIELD
        )

        # ── Result Output Card ───────────────────────────────────────
        result_card = ctk.CTkFrame(
            main_frame, fg_color=SURFACE, corner_radius=14,
            border_width=1, border_color=BORDER
        )
        result_card.pack(fill=ctk.BOTH, expand=True, pady=(0, 16), padx=2)

        res_header = ctk.CTkFrame(result_card, fg_color="transparent")
        res_header.pack(fill=ctk.X, padx=14, pady=(12, 6))
        ctk.CTkLabel(res_header, text="✨ Refined Output", font=("Inter", 13, "bold"), text_color=ACCENT).pack(side=ctk.LEFT)

        quick_copy = ctk.CTkButton(
            res_header, text="📋 Copy", width=70, height=28,
            fg_color=FIELD, hover_color=OVERLAY, text_color=TEXT,
            border_color=BORDER, border_width=1, corner_radius=6, font=("Inter", 11),
            command=self.copy_to_clipboard
        )
        quick_copy.pack(side=ctk.RIGHT)

        self.char_count_lbl = ctk.CTkLabel(res_header, text="0 words", font=("Inter", 11), text_color=MUTED)
        self.char_count_lbl.pack(side=ctk.RIGHT, padx=(0, 10))

        self.result_text = ctk.CTkTextbox(
            result_card, height=140, fg_color=FIELD, text_color=TEXT,
            font=("Inter", 13), corner_radius=8, wrap="word",
            border_width=1, border_color=BORDER
        )
        self.result_text.pack(fill=ctk.BOTH, expand=True, padx=14, pady=(0, 14))

        # ── PWD Uttarakhand Glossary Card ────────────────────────────
        self._build_pwd_card(main_frame)

        # ── Footer Toolbar ───────────────────────────────────────────
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(fill=ctk.X)

        ctk.CTkButton(
            footer, text="Copy to Clipboard", command=self.copy_to_clipboard,
            fg_color=SURFACE, text_color=TEXT, hover_color=OVERLAY,
            border_color=BORDER, border_width=1, corner_radius=8, height=36, font=("Inter", 12)
        ).pack(side=ctk.LEFT, padx=(0, 8))

        # Optional Audio to Ideas entry
        try:
            from audio_to_idea.config import load_settings
            enabled = load_settings().data["integration"]["enabled"]
        except Exception:
            enabled = False
        if enabled:
            button = ctk.CTkButton(
                footer, text="Audio to Ideas", command=self.open_audio_to_idea,
                fg_color=SURFACE, text_color=TEXT, hover_color=OVERLAY,
                border_color=BORDER, border_width=1, corner_radius=8, height=36, font=("Inter", 12)
            )
            button.pack(side=ctk.LEFT, padx=(0, 8))
            try:
                from audio_to_idea.gui import Tooltip
                Tooltip(button, "Process saved recordings into timestamped transcripts and ideas. Settings are separate.")
            except Exception:
                pass

        ctk.CTkButton(
            footer, text="Settings", command=self.open_settings,
            fg_color=SURFACE, text_color=TEXT, hover_color=OVERLAY,
            border_color=BORDER, border_width=1, corner_radius=8, height=36, font=("Inter", 12)
        ).pack(side=ctk.RIGHT)

    def _build_pwd_card(self, parent):
        """Constructs the interactive PWD Uttarakhand Terminology & Glossary card."""
        self.pwd_card = ctk.CTkFrame(
            parent, fg_color=SURFACE, corner_radius=14,
            border_width=1, border_color=BORDER
        )
        self.pwd_card.pack(fill=ctk.X, pady=(0, 14), padx=2)

        pwd_header = ctk.CTkFrame(self.pwd_card, fg_color="transparent")
        pwd_header.pack(fill=ctk.X, padx=14, pady=(10, 4))
        ctk.CTkLabel(pwd_header, text="🏛 PWD Terminology & Glossary", font=("Inter", 13, "bold"), text_color=ACCENT).pack(side=ctk.LEFT)

        try:
            import pwd_helper
            term_count = len(pwd_helper.get_pwd_dict())
        except Exception:
            term_count = 53

        ctk.CTkLabel(pwd_header, text=f"{term_count} terms", font=("Inter", 10, "bold"),
                     fg_color=FIELD, text_color=MUTED, corner_radius=6, padx=8, pady=2).pack(side=ctk.RIGHT)

        search_box = ctk.CTkFrame(self.pwd_card, fg_color="transparent")
        search_box.pack(fill=ctk.X, padx=14, pady=(2, 6))

        self.pwd_search_var = tk.StringVar()
        self.pwd_search_entry = ctk.CTkEntry(
            search_box, textvariable=self.pwd_search_var,
            placeholder_text="Quick lookup (e.g. EE, NIT, SOR, MB, RCC, PMGSY)...",
            fg_color=FIELD, border_color=BORDER, border_width=1, corner_radius=8,
            text_color=TEXT, height=32, font=("Inter", 12)
        )
        self.pwd_search_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 8))
        self.pwd_search_var.trace_add("write", self._on_pwd_search)

        self.pwd_copy_btn = ctk.CTkButton(
            search_box, text="📋 Copy", width=70, height=32,
            fg_color=FIELD, hover_color=OVERLAY, text_color=TEXT,
            border_color=BORDER, border_width=1, corner_radius=8, font=("Inter", 11),
            command=self._copy_pwd_result
        )
        self.pwd_copy_btn.pack(side=ctk.RIGHT)

        self.pwd_result_lbl = ctk.CTkLabel(
            self.pwd_card, text="Type a PWD abbreviation above for instant English expansion & Hindi designation.",
            font=("Inter", 11), text_color=MUTED, wraplength=560, justify="left"
        )
        self.pwd_result_lbl.pack(fill=ctk.X, padx=14, pady=(0, 10), anchor="w")
        self._current_pwd_text = ""

    def _on_pwd_search(self, *_):
        query = self.pwd_search_var.get().strip()
        if not query:
            self.pwd_result_lbl.configure(
                text="Type a PWD abbreviation above for instant English expansion & Hindi designation.",
                text_color=MUTED
            )
            self._current_pwd_text = ""
            return

        try:
            import pwd_helper
            exact = pwd_helper.lookup_abbreviation(query)
            if exact:
                self._current_pwd_text = f"{exact['abbr']} — {exact['meaning']}"
                self.pwd_result_lbl.configure(
                    text=f"[{exact['category'].upper()}] {exact['abbr']} = {exact['meaning']}",
                    text_color=GREEN
                )
                return

            matches = pwd_helper.search_abbreviations(query)
            if matches:
                top = list(matches.items())[:3]
                summary = " · ".join(f"{k}: {v['meaning']}" for k, v in top)
                if len(matches) > 3:
                    summary += f" (+{len(matches)-3} more)"
                self._current_pwd_text = summary
                self.pwd_result_lbl.configure(text=summary, text_color=TEXT)
            else:
                self._current_pwd_text = ""
                self.pwd_result_lbl.configure(
                    text=f"No matching PWD abbreviation for '{query}'",
                    text_color=YELLOW
                )
        except Exception as e:
            self.pwd_result_lbl.configure(text=f"Lookup error: {e}", text_color=RED)

    def _copy_pwd_result(self):
        if self._current_pwd_text:
            subprocess.run("xclip -selection clipboard", input=self._current_pwd_text.encode(), shell=True)
            messagebox.showinfo("Copied", f"Copied to clipboard:\n{self._current_pwd_text}")

    def set_visual_state(self, state_name):
        """Switches the animated visualizer state (idle, recording, processing, success)."""
        self.visual_state = state_name
        self.anim_start_time = time.time()
        self._animate()

    def _animate(self):
        """Unified 30 FPS animation loop handling Ear 👂, Brain 🧠, and Mic 🎙 states."""
        now = time.time()
        elapsed = now - self.anim_start_time

        if self.visual_state == "recording":
            # 👂 Listening Ear with dynamic pulsating acoustic waves
            pulse = 6 * np.sin(elapsed * 4.5)
            self.canvas.coords(self.indicator, 32 - pulse, 32 - pulse, 108 + pulse, 108 + pulse)
            self.canvas.itemconfig(self.indicator, fill=SURFACE, outline=RECORD_COLOR, width=2.5)

            # Ear glyph
            self.canvas.coords(self.center_glyph, 70, 70)
            self.canvas.itemconfig(self.center_glyph, text="👂", state="normal")

            # Pulsing acoustic wave arcs
            wave_phase = (elapsed * 3.5) % 3.0
            for i, arc_id in enumerate(self.soundwave_arcs):
                r_base = 44 + i * 12
                r = r_base + 4 * np.sin(elapsed * 4.5 + i * 0.7)
                self.canvas.coords(arc_id, 70 - r, 70 - r, 70 + r, 70 + r)
                col = RECORD_COLOR if (i <= int(wave_phase)) else OVERLAY
                self.canvas.itemconfig(arc_id, outline=col, state="normal")

            # Hide thinking sparks
            self.canvas.itemconfig(self.orbit_ring, state="hidden")
            for sp in self.spark_nodes:
                self.canvas.itemconfig(sp, state="hidden")

            self.anim_loop_id = self.root.after(33, self._animate)

        elif self.visual_state == "processing":
            # 🧠 Neural Brain with orbiting synapsing sparks
            breath = 3 * np.sin(elapsed * 3.0)
            self.canvas.coords(self.indicator, 32 - breath, 32 - breath, 108 + breath, 108 + breath)
            self.canvas.itemconfig(self.indicator, fill=SURFACE, outline=ACCENT_COLOR, width=2)

            # Brain glyph
            self.canvas.coords(self.center_glyph, 70, 70)
            self.canvas.itemconfig(self.center_glyph, text="🧠", state="normal")

            # Hide acoustic waves
            for arc_id in self.soundwave_arcs:
                self.canvas.itemconfig(arc_id, state="hidden")

            # Orbit ellipse
            self.canvas.coords(self.orbit_ring, 14, 38, 126, 102)
            self.canvas.itemconfig(self.orbit_ring, state="normal", outline=OVERLAY)

            # Orbiting spark nodes
            speed = 2.8
            for idx, sp in enumerate(self.spark_nodes):
                angle = elapsed * speed + (idx * (2 * np.pi / 3))
                sx = 70 + 44 * np.cos(angle)
                sy = 70 + 24 * np.sin(angle)
                self.canvas.coords(sp, sx - 4, sy - 4, sx + 4, sy + 4)
                self.canvas.itemconfig(sp, state="normal", fill=YELLOW if idx == 0 else ACCENT_COLOR)

            self.anim_loop_id = self.root.after(33, self._animate)

        elif self.visual_state == "success":
            # ✨ Completion sparkle
            self.canvas.coords(self.indicator, 32, 32, 108, 108)
            self.canvas.itemconfig(self.indicator, fill=SURFACE, outline=SUCCESS_COLOR, width=3)
            self.canvas.coords(self.center_glyph, 70, 70)
            self.canvas.itemconfig(self.center_glyph, text="✨", state="normal")

            for arc_id in self.soundwave_arcs:
                self.canvas.itemconfig(arc_id, state="hidden")
            self.canvas.itemconfig(self.orbit_ring, state="hidden")
            for sp in self.spark_nodes:
                self.canvas.itemconfig(sp, state="hidden")

        else:
            # 🎙 Standby / Idle
            self.canvas.coords(self.indicator, 32, 32, 108, 108)
            self.canvas.itemconfig(self.indicator, fill=SURFACE, outline=BORDER, width=2)
            self.canvas.coords(self.center_glyph, 70, 70)
            self.canvas.itemconfig(self.center_glyph, text="🎙", state="normal")

            for arc_id in self.soundwave_arcs:
                self.canvas.itemconfig(arc_id, state="hidden")
            self.canvas.itemconfig(self.orbit_ring, state="hidden")
            for sp in self.spark_nodes:
                self.canvas.itemconfig(sp, state="hidden")

    def pulse_animation(self):
        """Maintains backward compatibility with tests/external callers."""
        self.set_visual_state("recording")

    def start_voice_process(self):
        self.is_recording = True
        self.action_btn.configure(text="Stop Recording", fg_color=RECORD_COLOR, hover_color="#eba0ac")
        self.status_label.configure(text="🎙 Listening...", text_color=RECORD_COLOR)
        if hasattr(self, "sub_status_label"):
            self.sub_status_label.configure(text="Capturing speech in English, Hindi or mixed speech...")
        self.result_text.delete("1.0", tk.END)
        
        self.set_visual_state("recording")
        threading.Thread(target=self.run_voice_process, daemon=True).start()

    def toggle_recording(self):
        if not self.is_recording:
            self.start_voice_process()
        else:
            self.engine.stop_recording()

    def run_voice_process(self):
        try:
            # 1. Record
            wav_path = self.engine.record()
            self.is_recording = False # Audio part done
            
            # 2. Transcribe
            self.status_queue.put(("status", "🧠 Transcribing..."))
            self.status_queue.put(("progress_start", None))
            raw_text = self.engine.transcribe(wav_path)
            
            if not raw_text.strip():
                self.status_queue.put(("error", "No speech detected."))
                return

            # 3. Refine/Translate
            mode = self.engine.config.get("MODE", "refine")
            status_msg = "🌍 Translating..." if mode == "translate" else "🧠 Refining thoughts..."
            self.status_queue.put(("status", status_msg))
            
            final_text = self.engine.refine(raw_text)
            
            # 4. Finalize
            self.status_queue.put(("result", final_text))
            
            # 5. Success actions
            subprocess.run("xclip -selection clipboard", input=final_text.encode(), shell=True)
            subprocess.run(["paplay", os.path.join(self.script_dir, "sounds", "complete.oga")])
                
        except Exception as e:
            self.status_queue.put(("error", str(e)))

    def check_queue(self):
        try:
            while True:
                msg_type, data = self.status_queue.get_nowait()
                if msg_type == "status":
                    self.status_label.configure(text=data, text_color=ACCENT_COLOR)
                    if hasattr(self, "sub_status_label"):
                        self.sub_status_label.configure(text="Local AI model is thinking and structuring...")
                elif msg_type == "progress_start":
                    self.progress.pack(pady=10); self.progress.start()
                    self.action_btn.configure(state="disabled", text="Thinking...")
                    self.set_visual_state("processing")
                elif msg_type == "result":
                    self.finish_task(data)
                elif msg_type == "error":
                    self.finish_task(f"❌ {data}", is_error=True)
        except queue.Empty: pass
        self.root.after(100, self.check_queue)

    def finish_task(self, text, is_error=False):
        self.is_recording = False
        self.progress.stop(); self.progress.pack_forget()
        self.action_btn.configure(state="normal", text="Start Recording", fg_color=ACCENT_COLOR, hover_color=PRIMARY_HOVER)
        
        if is_error:
            self.status_label.configure(text="Error", text_color=RECORD_COLOR)
            if hasattr(self, "sub_status_label"):
                self.sub_status_label.configure(text="Something went wrong during processing")
            self.set_visual_state("idle")
        else:
            self.status_label.configure(text="✅ Done & Copied!", text_color=SUCCESS_COLOR)
            words = len(text.strip().split())
            chars = len(text.strip())
            if hasattr(self, "sub_status_label"):
                self.sub_status_label.configure(text=f"{words} words ({chars} chars) copied to clipboard")
            if hasattr(self, "char_count_lbl"):
                self.char_count_lbl.configure(text=f"{words} words · {chars} chars")
            self.set_visual_state("success")
            self.root.after(2500, lambda: self.set_visual_state("idle") if self.visual_state == "success" else None)
            
        self.result_text.insert(tk.END, text)

    def copy_to_clipboard(self):
        text = self.result_text.get("1.0", tk.END).strip()
        if text:
            subprocess.run("xclip -selection clipboard", input=text.encode(), shell=True)
            messagebox.showinfo("Copied", "Text copied to clipboard!")

    def open_settings(self):
        try:
            import config_web_launcher
            config_web_launcher.launch_settings_app()
        except Exception:
            subprocess.Popen([sys.executable, os.path.join(self.script_dir, "config_gui.py")])

    def open_audio_to_idea(self):
        subprocess.Popen([sys.executable, "-m", "audio_to_idea", "gui"], cwd=self.script_dir)

    def open_manual(self):
        try:
            from manual_service import manual_service
            manual_service.open_in_browser()
        except Exception as e:
            subprocess.Popen([sys.executable, os.path.join(self.script_dir, "manual_gui.py")])

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk(); app = VoiceAssistantGUI(root); root.mainloop()


