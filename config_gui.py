#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
import requests
import utils

# Path to config file
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

def load_config():
    return utils.load_config(script_dir)

def save_config(config):
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    messagebox.showinfo("Success", "Configuration saved successfully!")

def get_ollama_models(host="http://localhost:11434"):
    try:
        response = requests.get(f"{host}/api/tags", timeout=2)
        if response.status_code == 200:
            return [m["name"] for m in response.json()["models"]]
    except:
        pass
    
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")[1:]
        return [line.split()[0] for line in lines if line]
    except:
        return ["qwen2.5:3b", "qwen3.5:0.8b", "mashriram/sarvam-1:latest"]

class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant Settings")
        self.root.geometry("550x800")
        
        self.config = load_config()
        
        # UI Elements
        canvas = tk.Canvas(root, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame = scrollable_frame
        
        # Section: Whisper
        self.add_section_header(frame, "🎙 Speech-to-Text", 0)
        
        ttk.Label(frame, text="Whisper Model:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=20)
        self.whisper_var = tk.StringVar(value=self.config["WHISPER_MODEL"])
        whisper_models = ["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"]
        self.whisper_cb = ttk.Combobox(frame, textvariable=self.whisper_var, values=whisper_models, width=30)
        self.whisper_cb.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Section: Refinement Models
        self.add_section_header(frame, "✨ Refinement Models (Cleanup)", 2)
        
        ttk.Label(frame, text="English Refiner:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=20)
        self.ollama_en_var = tk.StringVar(value=self.config["OLLAMA_MODELS"].get("en", ""))
        self.ollama_en_cb = ttk.Combobox(frame, textvariable=self.ollama_en_var, width=30)
        self.ollama_en_cb.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(frame, text="Hindi Refiner:").grid(row=4, column=0, sticky=tk.W, pady=5, padx=20)
        self.ollama_hi_var = tk.StringVar(value=self.config["OLLAMA_MODELS"].get("hi", ""))
        self.ollama_hi_cb = ttk.Combobox(frame, textvariable=self.ollama_hi_var, width=30)
        self.ollama_hi_cb.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)

        # Section: Translation Models
        self.add_section_header(frame, "🌍 Translation Models", 5)
        
        ttk.Label(frame, text="To English:").grid(row=6, column=0, sticky=tk.W, pady=5, padx=20)
        self.trans_en_var = tk.StringVar(value=self.config["OLLAMA_TRANSLATE_MODELS"].get("to_en", ""))
        self.trans_en_cb = ttk.Combobox(frame, textvariable=self.trans_en_var, width=30)
        self.trans_en_cb.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(frame, text="To Hindi:").grid(row=7, column=0, sticky=tk.W, pady=5, padx=20)
        self.trans_hi_var = tk.StringVar(value=self.config["OLLAMA_TRANSLATE_MODELS"].get("to_hi", ""))
        self.trans_hi_cb = ttk.Combobox(frame, textvariable=self.trans_hi_var, width=30)
        self.trans_hi_cb.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=5)

        # Section: AI Parameters
        self.add_section_header(frame, "⚙️ AI Parameters", 8)

        ttk.Label(frame, text="Ollama Host:").grid(row=9, column=0, sticky=tk.W, pady=5, padx=20)
        self.host_var = tk.StringVar(value=self.config["OLLAMA_HOST"])
        self.host_entry = ttk.Entry(frame, textvariable=self.host_var, width=30)
        self.host_entry.grid(row=9, column=1, sticky=(tk.W, tk.E), pady=5)
        self.host_var.trace_add("write", self.update_models)

        ttk.Label(frame, text="AI Temperature:").grid(row=10, column=0, sticky=tk.W, pady=5, padx=20)
        self.temp_var = tk.DoubleVar(value=self.config["TEMPERATURE"])
        self.temp_entry = ttk.Entry(frame, textvariable=self.temp_var, width=30)
        self.temp_entry.grid(row=10, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(frame, text="Default Mode:").grid(row=11, column=0, sticky=tk.W, pady=5, padx=20)
        self.mode_var = tk.StringVar(value=self.config.get("MODE", "refine"))
        self.mode_cb = ttk.Combobox(frame, textvariable=self.mode_var, values=["refine", "translate"], width=30)
        self.mode_cb.grid(row=11, column=1, sticky=(tk.W, tk.E), pady=5)

        # Section: Audio
        self.add_section_header(frame, "🔉 Audio Settings", 12)

        ttk.Label(frame, text="Silence Threshold:").grid(row=13, column=0, sticky=tk.W, pady=5, padx=20)
        self.threshold_var = tk.IntVar(value=self.config["SILENCE_THRESHOLD"])
        self.threshold_scale = ttk.Scale(frame, from_=50, to=1000, variable=self.threshold_var, orient=tk.HORIZONTAL)
        self.threshold_scale.grid(row=13, column=1, sticky=(tk.W, tk.E), pady=5)

        # Section: Storage
        self.add_section_header(frame, "📁 Storage & Backup", 14)

        ttk.Label(frame, text="Save to Markdown:").grid(row=15, column=0, sticky=tk.W, pady=5, padx=20)
        self.save_md_var = tk.BooleanVar(value=self.config.get("SAVE_TO_MARKDOWN", False))
        ttk.Checkbutton(frame, variable=self.save_md_var).grid(row=15, column=1, sticky=tk.W, pady=5)

        ttk.Label(frame, text="Markdown Path:").grid(row=16, column=0, sticky=tk.W, pady=5, padx=20)
        self.md_path_var = tk.StringVar(value=self.config.get("MARKDOWN_PATH", "~/Documents/VoiceNotes"))
        ttk.Entry(frame, textvariable=self.md_path_var, width=30).grid(row=16, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Buttons Frame
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=17, column=0, columnspan=2, pady=40)

        ttk.Button(btn_frame, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.root.destroy).pack(side=tk.LEFT, padx=10)

        self.update_models()

    def add_section_header(self, frame, text, row):
        header = ttk.Label(frame, text=text, font=("Inter", 11, "bold"), foreground="#89b4fa")
        header.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))

    def update_models(self, *args):
        models = get_ollama_models(self.host_var.get())
        for cb in [self.ollama_en_cb, self.ollama_hi_cb, self.trans_en_cb, self.trans_hi_cb]:
            cb["values"] = models

    def save_settings(self):
        try:
            new_config = {
                "SAMPLE_RATE": self.config["SAMPLE_RATE"],
                "WHISPER_MODEL": self.whisper_var.get(),
                "OLLAMA_MODELS": {
                    "en": self.ollama_en_var.get(),
                    "hi": self.ollama_hi_var.get()
                },
                "OLLAMA_TRANSLATE_MODELS": {
                    "to_en": self.trans_en_var.get(),
                    "to_hi": self.trans_hi_var.get()
                },
                "OLLAMA_HOST": self.host_var.get(),
                "SILENCE_THRESHOLD": self.threshold_var.get(),
                "SILENCE_DURATION": float(self.config["SILENCE_DURATION"]),
                "TEMPERATURE": float(self.temp_var.get()),
                "MODE": self.mode_var.get(),
                "SAVE_TO_MARKDOWN": self.save_md_var.get(),
                "MARKDOWN_PATH": self.md_path_var.get()
            }
            save_config(new_config)
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    # Basic dark theme for the settings
    root.configure(bg="#1e1e2e")
    app = ConfigApp(root)
    root.mainloop()
