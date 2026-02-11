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
        "OLLAMA_MODEL": "qwen2.5:3b",
        "OLLAMA_HOST": "http://localhost:11434",
        "SILENCE_THRESHOLD": 300,
        "SILENCE_DURATION": 2,
        "TEMPERATURE": 0.1
    }
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                return {**default_config, **json.load(f)}
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
        return ["qwen2.5:3b", "llama3", "mistral"]

class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant Settings")
        self.root.geometry("450x600")
        
        self.config = load_config()
        
        # UI Elements
        frame = ttk.Frame(root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Whisper Model
        ttk.Label(frame, text="Whisper Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.whisper_var = tk.StringVar(value=self.config["WHISPER_MODEL"])
        whisper_models = ["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"]
        self.whisper_cb = ttk.Combobox(frame, textvariable=self.whisper_var, values=whisper_models)
        self.whisper_cb.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Ollama Host
        ttk.Label(frame, text="Ollama Host:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.host_var = tk.StringVar(value=self.config["OLLAMA_HOST"])
        self.host_entry = ttk.Entry(frame, textvariable=self.host_var)
        self.host_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.host_var.trace_add("write", self.update_models)

        # Ollama Model
        ttk.Label(frame, text="Ollama Model:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ollama_var = tk.StringVar(value=self.config["OLLAMA_MODEL"])
        self.ollama_cb = ttk.Combobox(frame, textvariable=self.ollama_var)
        self.ollama_cb.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.update_models()
        
        # Silence Threshold
        ttk.Label(frame, text="Silence Threshold:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.threshold_var = tk.IntVar(value=self.config["SILENCE_THRESHOLD"])
        self.threshold_scale = ttk.Scale(frame, from_=50, to=1000, variable=self.threshold_var, orient=tk.HORIZONTAL)
        self.threshold_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        self.threshold_label = ttk.Label(frame, text=str(self.config["SILENCE_THRESHOLD"]))
        self.threshold_label.grid(row=3, column=2, padx=5)
        self.threshold_var.trace_add("write", lambda *args: self.threshold_label.config(text=str(self.threshold_var.get())))

        # Silence Duration
        ttk.Label(frame, text="Silence Duration (s):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.duration_var = tk.DoubleVar(value=self.config["SILENCE_DURATION"])
        self.duration_entry = ttk.Entry(frame, textvariable=self.duration_var)
        self.duration_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)

        # Temperature
        ttk.Label(frame, text="AI Temperature:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.temp_var = tk.DoubleVar(value=self.config["TEMPERATURE"])
        self.temp_entry = ttk.Entry(frame, textvariable=self.temp_var)
        self.temp_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)

        # Save Button
        self.save_btn = ttk.Button(frame, text="Save Settings", command=self.save_settings)
        self.save_btn.grid(row=6, column=0, columnspan=2, pady=20)

    def update_models(self, *args):
        models = get_ollama_models(self.host_var.get())
        self.ollama_cb["values"] = models
        if self.ollama_var.get() not in models and models:
            self.ollama_var.set(models[0])

    def save_settings(self):
        new_config = {
            "SAMPLE_RATE": self.config["SAMPLE_RATE"],
            "WHISPER_MODEL": self.whisper_var.get(),
            "OLLAMA_MODEL": self.ollama_var.get(),
            "OLLAMA_HOST": self.host_var.get(),
            "SILENCE_THRESHOLD": self.threshold_var.get(),
            "SILENCE_DURATION": self.duration_var.get(),
            "TEMPERATURE": self.temp_var.get()
        }
        save_config(new_config)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigApp(root)
    root.mainloop()