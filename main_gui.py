#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import os
import subprocess
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel
import utils
import time

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
        self.config = utils.load_config(self.script_dir)
        
        # Internal State
        self.is_recording = False
        self.worker_thread = None
        self.status_queue = queue.Queue()
        self.recording_stop_event = threading.Event()
        
        self.setup_ui()
        self.check_queue()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=("Inter", 12))
        style.configure("Status.TLabel", font=("Inter", 14, "bold"))
        style.configure("Action.TButton", font=("Inter", 12, "bold"), padding=10)
        
        # Main Container
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header & Status
        self.status_label = ttk.Label(main_frame, text="Ready", style="Status.TLabel")
        self.status_label.pack(pady=(0, 20))

        # 2. Visual Indicator (Canvas for Pulse/Animation)
        self.canvas = tk.Canvas(main_frame, width=150, height=150, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(pady=20)
        self.indicator = self.canvas.create_oval(25, 25, 125, 125, fill=ACCENT_COLOR, outline="")
        
        # 3. Main Action Button
        self.action_btn = tk.Button(
            main_frame, text="Start Recording", 
            command=self.toggle_recording,
            bg=ACCENT_COLOR, fg=BG_COLOR,
            font=("Inter", 14, "bold"),
            relief=tk.FLAT, padx=20, pady=10,
            cursor="hand2"
        )
        self.action_btn.pack(pady=20)

        # 4. Progress Bar (Analyzing Animation)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=300)
        
        # 5. Result Area
        ttk.Label(main_frame, text="Refined Text:").pack(anchor=tk.W, pady=(20, 5))
        self.result_text = tk.Text(
            main_frame, height=10, bg="#313244", fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR, font=("Inter", 11),
            padx=10, pady=10, relief=tk.FLAT, wrap=tk.WORD
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 6. Footer Buttons
        footer = ttk.Frame(main_frame)
        footer.pack(fill=tk.X, pady=(20, 0))
        
        self.copy_btn = tk.Button(
            footer, text="Copy to Clipboard", command=self.copy_to_clipboard,
            bg="#45475a", fg=TEXT_COLOR, relief=tk.FLAT, padx=15
        )
        self.copy_btn.pack(side=tk.LEFT)

        tk.Button(
            footer, text="Settings", command=self.open_settings,
            bg="#45475a", fg=TEXT_COLOR, relief=tk.FLAT, padx=15
        ).pack(side=tk.RIGHT)

    # --- Business Logic ---

    def toggle_recording(self):
        if not self.is_recording:
            self.start_voice_task()
        else:
            self.stop_manually()

    def start_voice_task(self):
        self.is_recording = True
        self.recording_stop_event.clear()
        self.action_btn.config(text="Stop Recording", bg=RECORD_COLOR)
        self.status_label.config(text="🎙 Listening...", foreground=RECORD_COLOR)
        self.result_text.delete("1.0", tk.END)
        
        # Start background thread
        self.worker_thread = threading.Thread(target=self.voice_process_thread, daemon=True)
        self.worker_thread.start()
        self.pulse_animation()

    def stop_manually(self):
        self.recording_stop_event.set()
        self.status_label.config(text="Stopping...")

    def pulse_animation(self):
        if not self.is_recording:
            self.canvas.itemconfig(self.indicator, fill=ACCENT_COLOR)
            return
        
        # Simple pulsing effect
        current_color = self.canvas.itemcget(self.indicator, "fill")
        next_color = "#f38ba8" if current_color != "#f38ba8" else "#eba0ac"
        self.canvas.itemconfig(self.indicator, fill=next_color)
        self.root.after(500, self.pulse_animation)

    def voice_process_thread(self):
        try:
            # 1. Recording
            self.record_audio()
            
            # 2. Analyzing
            self.status_queue.put(("status", "🧠 Analyzing..."))
            self.status_queue.put(("progress_start", None))
            
            # Transcribe
            model_size = self.config.get("WHISPER_MODEL", "large-v3-turbo")
            model = WhisperModel(model_size, compute_type="int8")
            segments, _ = model.transcribe(os.path.join(self.script_dir, "input.wav"))
            raw_text = " ".join(seg.text for seg in segments)
            
            if not raw_text.strip():
                self.status_queue.put(("error", "No speech detected."))
                return

            # Refine
            lang = utils.detect_lang(raw_text)
            model_name = utils.get_model_for_lang(self.config, lang)
            prompt, stops = utils.get_prompt_and_stops(self.script_dir, model_name, raw_text, lang)
            
            response = utils.call_ollama(
                self.config.get("OLLAMA_HOST"), model_name, prompt, stops, 
                self.config.get("TEMPERATURE", 0.1)
            )
            
            if "error" in response:
                self.status_queue.put(("error", response["error"]))
            else:
                final_text = utils.clean_response(response.get("response", ""))
                self.status_queue.put(("result", final_text))
                
        except Exception as e:
            self.status_queue.put(("error", str(e)))

    def record_audio(self):
        samplerate = self.config.get("SAMPLE_RATE", 16000)
        threshold = self.config.get("SILENCE_THRESHOLD", 300)
        silence_dur = self.config.get("SILENCE_DURATION", 2.0)
        chunk_size = 1024
        
        audio_buffer = []
        silent_chunks = 0
        
        # Sound 1: Start
        subprocess.run(["paplay", os.path.join(self.script_dir, "sounds", "start.oga")])
        
        with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', blocksize=chunk_size) as stream:
            while not self.recording_stop_event.is_set():
                chunk, _ = stream.read(chunk_size)
                audio_buffer.append(chunk)
                
                energy = np.sqrt(np.mean(chunk.astype(float)**2))
                if energy < threshold:
                    silent_chunks += 1
                    if (silent_chunks * chunk_size / samplerate) >= silence_dur:
                        break
                else:
                    silent_chunks = 0
        
        # Sound 2: End
        subprocess.run(["paplay", os.path.join(self.script_dir, "sounds", "end.oga")])
        
        audio = np.concatenate(audio_buffer)
        wav.write(os.path.join(self.script_dir, "input.wav"), samplerate, audio)
        self.is_recording = False

    def check_queue(self):
        try:
            while True:
                msg_type, data = self.status_queue.get_nowait()
                if msg_type == "status":
                    self.status_label.config(text=data, foreground=ACCENT_COLOR)
                elif msg_type == "progress_start":
                    self.progress.pack(pady=10)
                    self.progress.start(10)
                    self.action_btn.config(state=tk.DISABLED, text="Processing...")
                elif msg_type == "result":
                    self.finish_task(data)
                elif msg_type == "error":
                    self.finish_task(f"❌ Error: {data}", is_error=True)
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def finish_task(self, text, is_error=False):
        self.is_recording = False
        self.progress.stop()
        self.progress.pack_forget()
        self.action_btn.config(state=tk.NORMAL, text="Start Recording", bg=ACCENT_COLOR)
        
        if is_error:
            self.status_label.config(text="Error", foreground=RECORD_COLOR)
            self.result_text.insert(tk.END, text)
        else:
            self.status_label.config(text="✅ Done!", foreground=SUCCESS_COLOR)
            self.result_text.insert(tk.END, text)
            # Auto-copy
            subprocess.run("xclip -selection clipboard", input=text.encode(), shell=True)
            subprocess.run(["paplay", os.path.join(self.script_dir, "sounds", "complete.oga")])

    def copy_to_clipboard(self):
        text = self.result_text.get("1.0", tk.END).strip()
        if text:
            subprocess.run("xclip -selection clipboard", input=text.encode(), shell=True)
            messagebox.showinfo("Copied", "Text copied to clipboard!")

    def open_settings(self):
        subprocess.Popen(["python3", os.path.join(self.script_dir, "config_gui.py")])

if __name__ == "__main__":
    root = tk.Tk()
    # Set app icon if available or just a title
    app = VoiceAssistantGUI(root)
    root.mainloop()
