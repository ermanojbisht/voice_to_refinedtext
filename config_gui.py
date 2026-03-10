#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
import requests

# Path to config file
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

def load_config():
    default_config = {
        "SAMPLE_RATE": 16000,
        "WHISPER_MODEL": "large-v3-turbo",
        "OLLAMA_MODELS": {
            "en": "qwen3.5:0.8b",
            "hi": "mashriram/sarvam-1:latest"
        },
        "OLLAMA_HOST": "http://localhost:11434",
        "SILENCE_THRESHOLD": 300,
        "SILENCE_DURATION": 2,
        "TEMPERATURE": 0.1
    }
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                user_config = json.load(f)
                # Handle old single model config for migration
                if "OLLAMA_MODEL" in user_config and "OLLAMA_MODELS" not in user_config:
                    model = user_config.pop("OLLAMA_MODEL")
                    user_config["OLLAMA_MODELS"] = {"en": model, "hi": model}
                
                return {**default_config, **user_config}
            except:
                return default_config
    return default_config

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
        self.root.geometry("520x650") # Wider window
        
        self.config = load_config()
        
        # UI Elements
        frame = ttk.Frame(root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1) # Make second column expandable
        
        # Whisper Model
        ttk.Label(frame, text="Whisper Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.whisper_var = tk.StringVar(value=self.config["WHISPER_MODEL"])
        whisper_models = ["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"]
        self.whisper_cb = ttk.Combobox(frame, textvariable=self.whisper_var, values=whisper_models, width=30)
        self.whisper_cb.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Ollama Host
        ttk.Label(frame, text="Ollama Host:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.host_var = tk.StringVar(value=self.config["OLLAMA_HOST"])
        self.host_entry = ttk.Entry(frame, textvariable=self.host_var, width=30)
        self.host_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.host_var.trace_add("write", self.update_models)

        # Ollama Model (English)
        ttk.Label(frame, text="Ollama (English):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ollama_en_var = tk.StringVar(value=self.config["OLLAMA_MODELS"].get("en", ""))
        self.ollama_en_cb = ttk.Combobox(frame, textvariable=self.ollama_en_var, width=30)
        self.ollama_en_cb.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        # Ollama Model (Hindi)
        ttk.Label(frame, text="Ollama (Hindi):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ollama_hi_var = tk.StringVar(value=self.config["OLLAMA_MODELS"].get("hi", ""))
        self.ollama_hi_cb = ttk.Combobox(frame, textvariable=self.ollama_hi_var, width=30)
        self.ollama_hi_cb.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.update_models()
        
        # Silence Threshold
        ttk.Label(frame, text="Silence Threshold:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.threshold_var = tk.IntVar(value=self.config["SILENCE_THRESHOLD"])
        self.threshold_scale = ttk.Scale(frame, from_=50, to=1000, variable=self.threshold_var, orient=tk.HORIZONTAL)
        self.threshold_scale.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        self.threshold_label = ttk.Label(frame, text=str(self.config["SILENCE_THRESHOLD"]))
        self.threshold_label.grid(row=4, column=2, padx=5)
        self.threshold_var.trace_add("write", lambda *args: self.threshold_label.config(text=str(self.threshold_var.get())))

        # Silence Duration
        ttk.Label(frame, text="Silence Duration (s):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.duration_var = tk.DoubleVar(value=self.config["SILENCE_DURATION"])
        self.duration_entry = ttk.Entry(frame, textvariable=self.duration_var, width=30)
        self.duration_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)

        # Temperature
        ttk.Label(frame, text="AI Temperature:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.temp_var = tk.DoubleVar(value=self.config["TEMPERATURE"])
        self.temp_entry = ttk.Entry(frame, textvariable=self.temp_var, width=30)
        self.temp_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)

        # Buttons Frame
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=30)

        # Save Button
        self.save_btn = ttk.Button(btn_frame, text="Save Settings", command=self.save_settings)
        self.save_btn.grid(row=0, column=0, padx=10)

        # Cancel Button
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.root.destroy)
        self.cancel_btn.grid(row=0, column=1, padx=10)

    def update_models(self, *args):
        models = get_ollama_models(self.host_var.get())
        self.ollama_en_cb["values"] = models
        self.ollama_hi_cb["values"] = models
        
        # Reset if model not found in current list
        if self.ollama_en_var.get() not in models and models:
             if "qwen3.5:0.8b" in models: self.ollama_en_var.set("qwen3.5:0.8b")
             else: self.ollama_en_var.set(models[0])
             
        if self.ollama_hi_var.get() not in models and models:
             if "mashriram/sarvam-1:latest" in models: self.ollama_hi_var.set("mashriram/sarvam-1:latest")
             else: self.ollama_hi_var.set(models[0])

    def save_settings(self):
        try:
            new_config = {
                "SAMPLE_RATE": self.config["SAMPLE_RATE"],
                "WHISPER_MODEL": self.whisper_var.get(),
                "OLLAMA_MODELS": {
                    "en": self.ollama_en_var.get(),
                    "hi": self.ollama_hi_var.get()
                },
                "OLLAMA_HOST": self.host_var.get(),
                "SILENCE_THRESHOLD": self.threshold_var.get(),
                "SILENCE_DURATION": self.duration_var.get(),
                "TEMPERATURE": self.temp_var.get()
            }
            save_config(new_config)
            self.root.destroy() # Close after save
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigApp(root)
    root.mainloop()
