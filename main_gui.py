#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
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
        self.root.configure(bg=BG_COLOR)
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.engine = VoiceEngine(self.script_dir)
        
        # Internal State
        self.is_recording = False
        self.status_queue = queue.Queue()
        
        self.setup_ui()
        self.check_queue()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=("Inter", 12))
        style.configure("Status.TLabel", font=("Inter", 14, "bold"))
        
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.status_label = ttk.Label(main_frame, text="Ready", style="Status.TLabel")
        self.status_label.pack(pady=(0, 20))

        self.canvas = tk.Canvas(main_frame, width=150, height=150, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(pady=20)
        self.indicator = self.canvas.create_oval(25, 25, 125, 125, fill=ACCENT_COLOR, outline="")
        
        self.action_btn = tk.Button(
            main_frame, text="Start Recording", 
            command=self.toggle_recording,
            bg=ACCENT_COLOR, fg=BG_COLOR,
            font=("Inter", 14, "bold"),
            relief=tk.FLAT, padx=20, pady=10, cursor="hand2"
        )
        self.action_btn.pack(pady=20)

        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=300)
        
        ttk.Label(main_frame, text="Refined Text:").pack(anchor=tk.W, pady=(20, 5))
        self.result_text = tk.Text(
            main_frame, height=10, bg="#313244", fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR, font=("Inter", 11),
            padx=10, pady=10, relief=tk.FLAT, wrap=tk.WORD
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        footer = ttk.Frame(main_frame)
        footer.pack(fill=tk.X, pady=(20, 0))
        
        tk.Button(footer, text="Copy to Clipboard", command=self.copy_to_clipboard,
                  bg="#45475a", fg=TEXT_COLOR, relief=tk.FLAT, padx=15).pack(side=tk.LEFT)

        tk.Button(footer, text="Settings", command=self.open_settings,
                  bg="#45475a", fg=TEXT_COLOR, relief=tk.FLAT, padx=15).pack(side=tk.RIGHT)

    def start_voice_process(self):
        self.is_recording = True
        self.action_btn.config(text="Stop Recording", bg=RECORD_COLOR)
        self.status_label.config(text="🎙 Listening...", foreground=RECORD_COLOR)
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
                    self.status_label.config(text=data, foreground=ACCENT_COLOR)
                elif msg_type == "progress_start":
                    self.progress.pack(pady=10); self.progress.start(10)
                    self.action_btn.config(state=tk.DISABLED, text="Processing...")
                elif msg_type == "result":
                    self.finish_task(data)
                elif msg_type == "error":
                    self.finish_task(f"❌ {data}", is_error=True)
        except queue.Empty: pass
        self.root.after(100, self.check_queue)

    def finish_task(self, text, is_error=False):
        self.is_recording = False
        self.progress.stop(); self.progress.pack_forget()
        self.action_btn.config(state=tk.NORMAL, text="Start Recording", bg=ACCENT_COLOR)
        self.status_label.config(text="Error" if is_error else "✅ Done!", 
                                foreground=RECORD_COLOR if is_error else SUCCESS_COLOR)
        self.result_text.insert(tk.END, text)

    def copy_to_clipboard(self):
        text = self.result_text.get("1.0", tk.END).strip()
        if text:
            subprocess.run("xclip -selection clipboard", input=text.encode(), shell=True)
            messagebox.showinfo("Copied", "Text copied to clipboard!")

    def open_settings(self):
        subprocess.Popen(["python3", os.path.join(self.script_dir, "config_gui.py")])

if __name__ == "__main__":
    root = tk.Tk(); app = VoiceAssistantGUI(root); root.mainloop()
