#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import queue
import os
import subprocess
import time
import numpy as np
from engine import VoiceEngine

# Colors
BG_COLOR = "#1e1e2e"
TEXT_COLOR = "#cdd6f4"
ACCENT_COLOR = "#89b4fa"
RECORD_COLOR = "#f38ba8"
SUCCESS_COLOR = "#a6e3a1"

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Refiner")
        self.root.geometry("600x750")
        self.root.configure(fg_color=BG_COLOR)
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.engine = VoiceEngine(self.script_dir)
        
        # Internal State
        self.is_recording = False
        self.status_queue = queue.Queue()
        
        self.setup_ui()
        self.check_queue()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=30, pady=30)

        self.status_label = ctk.CTkLabel(main_frame, text="Ready", text_color=TEXT_COLOR, font=("Inter", 16, "bold"))
        self.status_label.pack(pady=(0, 20))

        self.canvas = tk.Canvas(main_frame, width=150, height=150, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(pady=20)
        self.indicator = self.canvas.create_oval(25, 25, 125, 125, fill=ACCENT_COLOR, outline="")
        
        self.action_btn = ctk.CTkButton(
            main_frame, text="Start Recording", 
            command=self.toggle_recording,
            fg_color=ACCENT_COLOR, text_color=BG_COLOR,
            font=("Inter", 14, "bold"), hover_color="#b4befe",
            corner_radius=8, height=45
        )
        self.action_btn.pack(pady=20)

        self.progress = ctk.CTkProgressBar(main_frame, width=300, mode='indeterminate', progress_color=ACCENT_COLOR)
        
        ctk.CTkLabel(main_frame, text="Refined Text:", font=("Inter", 12)).pack(anchor=ctk.W, pady=(20, 5))
        self.result_text = ctk.CTkTextbox(
            main_frame, height=150, fg_color="#313244", text_color=TEXT_COLOR,
            font=("Inter", 13), corner_radius=8, wrap="word"
        )
        self.result_text.pack(fill=ctk.BOTH, expand=True)

        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(fill=ctk.X, pady=(20, 0))
        
        ctk.CTkButton(footer, text="Copy to Clipboard", command=self.copy_to_clipboard,
                  fg_color="#45475a", text_color=TEXT_COLOR, hover_color="#585b70",
                  corner_radius=8, height=35).pack(side=ctk.LEFT)

        ctk.CTkButton(footer, text="Settings", command=self.open_settings,
                  fg_color="#45475a", text_color=TEXT_COLOR, hover_color="#585b70",
                  corner_radius=8, height=35).pack(side=ctk.RIGHT)

    def start_voice_process(self):
        self.is_recording = True
        self.action_btn.configure(text="Stop Recording", fg_color=RECORD_COLOR, hover_color="#eba0ac")
        self.status_label.configure(text="🎙 Listening...", text_color=RECORD_COLOR)
        self.result_text.delete("1.0", tk.END)
        
        # Reset animation state
        self.pulse_start_time = time.time()
        self.pulse_animation()
        
        threading.Thread(target=self.run_voice_process, daemon=True).start()

    def pulse_animation(self):
        """Creates a smooth breathing effect for the recording indicator."""
        if not self.is_recording:
            # Reset to static idle state
            self.canvas.coords(self.indicator, 25, 25, 125, 125)
            self.canvas.itemconfig(self.indicator, fill=ACCENT_COLOR)
            return
        
        # Calculate expansion using a sine wave
        elapsed = time.time() - self.pulse_start_time
        # Speed: 4.0, Amplitude: 15 pixels
        expansion = 15 * (np.sin(elapsed * 4.0))
        
        # Coordinates: [x0, y0, x1, y1]
        x0, y0, x1, y1 = 25 - expansion, 25 - expansion, 125 + expansion, 125 + expansion
        self.canvas.coords(self.indicator, x0, y0, x1, y1)
        
        # Shift color slightly
        self.canvas.itemconfig(self.indicator, fill=RECORD_COLOR)
        
        # 30ms for ~33 FPS smoothness
        self.root.after(30, self.pulse_animation)

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
            status_msg = "🌍 Translating..." if mode == "translate" else "✨ Refining..."
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
                elif msg_type == "progress_start":
                    self.progress.pack(pady=10); self.progress.start()
                    self.action_btn.configure(state="disabled", text="Processing...")
                elif msg_type == "result":
                    self.finish_task(data)
                elif msg_type == "error":
                    self.finish_task(f"❌ {data}", is_error=True)
        except queue.Empty: pass
        self.root.after(100, self.check_queue)

    def finish_task(self, text, is_error=False):
        self.is_recording = False
        self.progress.stop(); self.progress.pack_forget()
        self.action_btn.configure(state="normal", text="Start Recording", fg_color=ACCENT_COLOR, hover_color="#b4befe")
        self.status_label.configure(text="Error" if is_error else "✅ Done!", 
                                text_color=RECORD_COLOR if is_error else SUCCESS_COLOR)
        self.result_text.insert(tk.END, text)

    def copy_to_clipboard(self):
        text = self.result_text.get("1.0", tk.END).strip()
        if text:
            subprocess.run("xclip -selection clipboard", input=text.encode(), shell=True)
            messagebox.showinfo("Copied", "Text copied to clipboard!")

    def open_settings(self):
        subprocess.Popen(["python3", os.path.join(self.script_dir, "config_gui.py")])

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk(); app = VoiceAssistantGUI(root); root.mainloop()
