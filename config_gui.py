#!/usr/bin/env python3
"""Settings window — two tabs:
  • Voice Refiner  — existing Whisper / Ollama / audio / storage settings
  • Evening Review — vault paths, review behaviour, per-step toggles
"""
import os
import json
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

import requests
import utils
import review_engine

script_dir  = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")
review_config_path = os.path.join(script_dir, "review_config.json")

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_main_config():
    return utils.load_config(script_dir)

def load_review_config_raw():
    if os.path.exists(review_config_path):
        try:
            with open(review_config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_ollama_models(host="http://localhost:11434"):
    try:
        r = requests.get(f"{host}/api/tags", timeout=2)
        if r.status_code == 200:
            return [m["name"] for m in r.json()["models"]]
    except Exception:
        pass
    try:
        out = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        lines = out.stdout.strip().split("\n")[1:]
        return [l.split()[0] for l in lines if l.strip()]
    except Exception:
        return ["qwen2.5:3b", "qwen3:0.6b", "gemma3:1b"]

# ── Palette ────────────────────────────────────────────────────────────────────
BG      = "#1e1e2e"
SURFACE = "#313244"
ACCENT  = "#89b4fa"
TEXT    = "#cdd6f4"
SUBTLE  = "#6c7086"
GREEN   = "#a6e3a1"

# ── Section header helper ──────────────────────────────────────────────────────

def _section(frame, text, row):
    lbl = ctk.CTkLabel(frame, text=text, font=("Inter", 14, "bold"), text_color=ACCENT)
    lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 6))

def _label(frame, text, row, col=0):
    ctk.CTkLabel(frame, text=text, text_color=TEXT, font=("Inter", 12)).grid(
        row=row, column=col, sticky="w", padx=20, pady=4)

def _note(frame, text, row):
    ctk.CTkLabel(frame, text=text, text_color=SUBTLE, font=("Inter", 11)).grid(
        row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 4))

# ── Main application ───────────────────────────────────────────────────────────

class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant — Settings")
        self.root.geometry("650x780")
        self.root.configure(fg_color=BG)

        self.main_cfg   = load_main_config()
        self.review_raw = load_review_config_raw()

        self._build_ui()
        self._load_ollama_models()

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(self.root, fg_color=SURFACE, segmented_button_selected_color=ACCENT, segmented_button_selected_hover_color="#b4befe")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self.tab1 = self.tabview.add("🎙 Voice Refiner")
        self.tab2 = self.tabview.add("🌙 Evening Review")

        # Scrollable frames for tabs
        self.scroll1 = ctk.CTkScrollableFrame(self.tab1, fg_color="transparent")
        self.scroll1.pack(fill="both", expand=True)
        self._build_voice_tab(self.scroll1)

        self.scroll2 = ctk.CTkScrollableFrame(self.tab2, fg_color="transparent")
        self.scroll2.pack(fill="both", expand=True)
        self._build_review_tab(self.scroll2)

        # Save / Cancel bar
        bar = ctk.CTkFrame(self.root, fg_color="transparent")
        bar.pack(fill="x", side="bottom", pady=(0, 20), padx=20)

        ctk.CTkButton(bar, text="Save All Settings", command=self._save_all,
                  fg_color=ACCENT, text_color=BG, font=("Inter", 14, "bold"),
                  hover_color="#b4befe", corner_radius=8, height=40).pack(side=ctk.LEFT, padx=(0, 10))
        
        ctk.CTkButton(bar, text="Cancel", command=self.root.destroy,
                  fg_color="#45475a", text_color=TEXT, font=("Inter", 14),
                  hover_color="#585b70", corner_radius=8, height=40).pack(side=ctk.LEFT)

    def _build_voice_tab(self, f):
        f.columnconfigure(1, weight=1)

        _section(f, "🎙  Speech-to-Text", 0)
        _label(f, "Whisper Model:", 1)
        self.whisper_var = ctk.StringVar(value=self.main_cfg.get("WHISPER_MODEL", "large-v3-turbo"))
        ctk.CTkComboBox(f, variable=self.whisper_var, width=250,
                     values=["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"]
                     ).grid(row=1, column=1, sticky="we", padx=20, pady=4)

        _section(f, "✨  Refinement Models", 2)
        _label(f, "English Refiner:", 3)
        self.en_model_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_MODELS", {}).get("en", ""))
        self.en_cb = ctk.CTkComboBox(f, variable=self.en_model_var, width=250)
        self.en_cb.grid(row=3, column=1, sticky="we", padx=20, pady=4)

        _label(f, "Hindi Refiner:", 4)
        self.hi_model_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_MODELS", {}).get("hi", ""))
        self.hi_cb = ctk.CTkComboBox(f, variable=self.hi_model_var, width=250)
        self.hi_cb.grid(row=4, column=1, sticky="we", padx=20, pady=4)

        _section(f, "🌍  Translation Models", 5)
        _label(f, "→ English:", 6)
        self.to_en_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_en", ""))
        self.to_en_cb = ctk.CTkComboBox(f, variable=self.to_en_var, width=250)
        self.to_en_cb.grid(row=6, column=1, sticky="we", padx=20, pady=4)

        _label(f, "→ Hindi:", 7)
        self.to_hi_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_hi", ""))
        self.to_hi_cb = ctk.CTkComboBox(f, variable=self.to_hi_var, width=250)
        self.to_hi_cb.grid(row=7, column=1, sticky="we", padx=20, pady=4)

        _section(f, "⚙️  AI Parameters", 8)
        _label(f, "Ollama Host:", 9)
        self.host_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_HOST", "http://localhost:11434"))
        host_entry = ctk.CTkEntry(f, textvariable=self.host_var, width=250)
        host_entry.grid(row=9, column=1, sticky="we", padx=20, pady=4)
        self.host_var.trace_add("write", lambda *_: self._load_ollama_models())

        _label(f, "Temperature:", 10)
        self.temp_var = ctk.DoubleVar(value=self.main_cfg.get("TEMPERATURE", 0.1))
        ctk.CTkEntry(f, textvariable=self.temp_var, width=250).grid(row=10, column=1, sticky="we", padx=20, pady=4)

        _label(f, "Default Mode:", 11)
        self.mode_var = ctk.StringVar(value=self.main_cfg.get("MODE", "refine"))
        ctk.CTkComboBox(f, variable=self.mode_var, values=["refine", "translate"], width=250).grid(row=11, column=1, sticky="we", padx=20, pady=4)

        _section(f, "🔉  Audio Settings", 12)
        _label(f, "Silence Threshold:", 13)
        self.threshold_var = ctk.IntVar(value=self.main_cfg.get("SILENCE_THRESHOLD", 300))
        ctk.CTkSlider(f, from_=50, to=1000, variable=self.threshold_var).grid(row=13, column=1, sticky="we", padx=20, pady=4)

        _label(f, "Silence Duration (s):", 14)
        self.silence_dur_var = ctk.DoubleVar(value=self.main_cfg.get("SILENCE_DURATION", 2.0))
        ctk.CTkEntry(f, textvariable=self.silence_dur_var, width=250).grid(row=14, column=1, sticky="we", padx=20, pady=4)

        _section(f, "📁  Storage & Output", 15)
        _label(f, "Save to Markdown:", 16)
        self.save_md_var = tk.BooleanVar(value=self.main_cfg.get("SAVE_TO_MARKDOWN", False))
        ctk.CTkCheckBox(f, text="", variable=self.save_md_var).grid(row=16, column=1, sticky="w", padx=20, pady=4)

        _label(f, "Markdown Path:", 17)
        self.md_path_var = ctk.StringVar(value=self.main_cfg.get("MARKDOWN_PATH", "~/Documents/VoiceNotes"))
        ctk.CTkEntry(f, textvariable=self.md_path_var, width=250).grid(row=17, column=1, sticky="we", padx=20, pady=4)

        _label(f, "Direct Typing:", 18)
        self.direct_typing_var = tk.BooleanVar(value=self.main_cfg.get("DIRECT_TYPING", False))
        ctk.CTkCheckBox(f, text="", variable=self.direct_typing_var).grid(row=18, column=1, sticky="w", padx=20, pady=4)
        _note(f, "Types refined text directly at cursor position after processing.", 19)

    def _build_review_tab(self, f):
        f.columnconfigure(1, weight=1)

        vp = self.review_raw.get("vault_paths", {})

        _section(f, "📂  Obsidian Vault Paths", 0)
        _note(f, "Use ~ for home directory. Folders are created automatically.", 1)

        _label(f, "Base Vault:", 2)
        self.vault_base_var = ctk.StringVar(value=vp.get("base_vault", "~/learning_vault"))
        ctk.CTkEntry(f, textvariable=self.vault_base_var, width=300).grid(row=2, column=1, sticky="we", padx=20, pady=4)

        _label(f, "Daily Notes:", 3)
        self.vault_daily_var = ctk.StringVar(value=vp.get("daily_notes", "~/learning_vault/My Daily Notes"))
        ctk.CTkEntry(f, textvariable=self.vault_daily_var, width=300).grid(row=3, column=1, sticky="we", padx=20, pady=4)

        _label(f, "Wellness Notes:", 4)
        self.vault_well_var = ctk.StringVar(value=vp.get("wellness_notes", "~/learning_vault/My Daily Notes/Wellness"))
        ctk.CTkEntry(f, textvariable=self.vault_well_var, width=300).grid(row=4, column=1, sticky="we", padx=20, pady=4)

        _section(f, "⚙️  Review Behaviour", 5)

        _label(f, "Session Expiry (hours):", 6)
        self.expiry_var = ctk.StringVar(value=str(self.review_raw.get("review_expiry_hours", 1)))
        ctk.CTkComboBox(f, variable=self.expiry_var, values=["1","2","3","4","5","6","7","8"], width=100).grid(row=6, column=1, sticky="w", padx=20, pady=4)
        _note(f, "Review state expires after this many hours of inactivity.", 7)

        _label(f, "Voice Narration:", 8)
        self.narration_var = tk.BooleanVar(value=self.review_raw.get("voice_narration", True))
        ctk.CTkCheckBox(f, text="", variable=self.narration_var).grid(row=8, column=1, sticky="w", padx=20, pady=4)
        _note(f, "Speak step prompts aloud when each review step begins.", 9)

        _label(f, "Context Days:", 10)
        self.context_days_var = ctk.StringVar(value=str(self.review_raw.get("last_n_days_context", 1)))
        ctk.CTkComboBox(f, variable=self.context_days_var, values=["1","2","3","4","5","6","7"], width=100).grid(row=10, column=1, sticky="w", padx=20, pady=4)
        _note(f, "How many previous days' notes the AI reads for context (Phase 2).", 11)

        _section(f, "🔊  Text-to-Speech (Step Narration)", 12)
        _note(f, "Engine used to narrate step prompts. Piper sounds natural; espeak is the fallback.", 13)

        _label(f, "TTS Engine:", 14)
        self.tts_engine_var = ctk.StringVar(value=self.review_raw.get("tts_engine", "espeak"))
        tts_cb = ctk.CTkComboBox(f, variable=self.tts_engine_var,
                                  values=["espeak", "piper"], width=150,
                                  command=self._on_tts_engine_change)
        tts_cb.grid(row=14, column=1, sticky="w", padx=20, pady=4)
        _note(f, "espeak: built-in, no setup needed.  piper: neural voice, needs model file.", 15)

        _label(f, "Piper Model Path:", 16)
        self.piper_model_var = ctk.StringVar(value=self.review_raw.get("piper_model", ""))
        self.piper_model_entry = ctk.CTkEntry(f, textvariable=self.piper_model_var, width=300,
                                               placeholder_text="e.g. ~/voice_to_refinedtext/models/en_US-lessac-medium.onnx")
        self.piper_model_entry.grid(row=16, column=1, sticky="we", padx=20, pady=4)
        self._piper_note = ctk.CTkLabel(f,
            text="Full path to the .onnx model file. The matching .onnx.json must be in the same folder.",
            text_color=SUBTLE, font=("Inter", 11), wraplength=380, justify="left")
        self._piper_note.grid(row=17, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 4))

        self._on_tts_engine_change(self.tts_engine_var.get())  # set initial visibility

        _section(f, "🤖  Step Structuring Model", 18)
        _note(f, "Which Ollama model converts your voice clips into formatted notes.", 19)
        _label(f, "Structuring Model:", 20)
        self.struct_model_var = ctk.StringVar(value=self.review_raw.get("structure_model", ""))
        self.struct_cb = ctk.CTkComboBox(f, variable=self.struct_model_var, width=300)
        self.struct_cb.grid(row=20, column=1, sticky="we", padx=20, pady=4)
        _note(f, "Leave blank to use the English Refiner model from Voice Refiner tab.", 21)

        _section(f, "📋  Step Configuration", 22)
        _note(f, "Toggle per-step behaviour. Step prompts are edited in review_config.json.", 23)

        hdr = ctk.CTkFrame(f, fg_color=SURFACE, corner_radius=6)
        hdr.grid(row=24, column=0, columnspan=2, sticky="we", padx=20, pady=(10, 4))
        for col_text, col_w in [("Step", 200), ("Skippable", 100), ("AI Refine", 100)]:
            ctk.CTkLabel(hdr, text=col_text, text_color=ACCENT, font=("Inter", 12, "bold"), width=col_w, anchor="w").pack(side=ctk.LEFT, padx=10, pady=6)

        full_cfg = review_engine.load_review_config(script_dir)
        self.step_skippable_vars = []
        self.step_refine_vars    = []
        self._step_ids           = []

        for row_i, step in enumerate(full_cfg.get("review_steps", [])):
            row_frame = ctk.CTkFrame(f, fg_color="transparent")
            row_frame.grid(row=25 + row_i, column=0, columnspan=2, sticky="we", padx=20, pady=2)

            ctk.CTkLabel(row_frame, text=f"{step['step_id']}. {step['section_name']}",
                     text_color=TEXT, font=("Inter", 12), width=200, anchor="w").pack(side=ctk.LEFT, padx=(10,0), pady=4)

            skip_var = tk.BooleanVar(value=step.get("skippable", True))
            ctk.CTkCheckBox(row_frame, text="", variable=skip_var, width=100).pack(side=ctk.LEFT, padx=(30, 0))

            refine_var = tk.BooleanVar(value=step.get("refine", True))
            ctk.CTkCheckBox(row_frame, text="", variable=refine_var, width=100).pack(side=ctk.LEFT, padx=(15, 0))

            self.step_skippable_vars.append(skip_var)
            self.step_refine_vars.append(refine_var)
            self._step_ids.append(step["step_id"])

    def _on_tts_engine_change(self, value):
        """Show/hide piper model path based on selected engine."""
        is_piper = value == "piper"
        state = "normal" if is_piper else "disabled"
        self.piper_model_entry.configure(state=state)
        color = TEXT if is_piper else SUBTLE
        self._piper_note.configure(text_color=color)

    def _load_ollama_models(self, *_):
        def _fetch():
            host   = getattr(self, "host_var", None)
            models = get_ollama_models(host.get() if host else "http://localhost:11434")
            self.root.after(0, lambda: self._populate_model_dropdowns(models))
        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _populate_model_dropdowns(self, models):
        for cb in (self.en_cb, self.hi_cb, self.to_en_cb, self.to_hi_cb):
            cb.configure(values=models)
        if hasattr(self, "struct_cb"):
            self.struct_cb.configure(values=[""] + models)

    def _save_all(self):
        errors = []
        try:
            new_main = {
                "SAMPLE_RATE":              self.main_cfg.get("SAMPLE_RATE", 16000),
                "WHISPER_MODEL":            self.whisper_var.get(),
                "OLLAMA_MODELS":            {"en": self.en_model_var.get(), "hi": self.hi_model_var.get()},
                "OLLAMA_TRANSLATE_MODELS":  {"to_en": self.to_en_var.get(), "to_hi": self.to_hi_var.get()},
                "OLLAMA_HOST":              self.host_var.get(),
                "SILENCE_THRESHOLD":        int(self.threshold_var.get()),
                "SILENCE_DURATION":         float(self.silence_dur_var.get()),
                "TEMPERATURE":              float(self.temp_var.get()),
                "MODE":                     self.mode_var.get(),
                "SAVE_TO_MARKDOWN":         self.save_md_var.get(),
                "MARKDOWN_PATH":            self.md_path_var.get(),
                "DIRECT_TYPING":            self.direct_typing_var.get(),
            }
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(new_main, fh, indent=4)
        except Exception as e:
            errors.append(f"config.json: {e}")

        try:
            # Start from the existing file so fields the GUI doesn't manage are preserved
            existing = load_review_config_raw()

            existing["vault_paths"] = {
                "base_vault":     self.vault_base_var.get().strip(),
                "daily_notes":    self.vault_daily_var.get().strip(),
                "wellness_notes": self.vault_well_var.get().strip(),
            }
            existing["review_expiry_hours"] = int(self.expiry_var.get())
            existing["voice_narration"]     = self.narration_var.get()
            existing["last_n_days_context"] = int(self.context_days_var.get())
            existing["tts_engine"]          = self.tts_engine_var.get()
            existing["piper_model"]         = self.piper_model_var.get().strip()

            struct_model = self.struct_model_var.get().strip()
            if struct_model:
                existing["structure_model"] = struct_model
            else:
                existing.pop("structure_model", None)

            # Merge per-step skippable/refine flags, preserving all other step fields
            existing_by_id = {s["step_id"]: s for s in existing.get("review_steps", []) if "step_id" in s}
            merged_steps = []
            for sid, skip_v, refine_v in zip(self._step_ids, self.step_skippable_vars, self.step_refine_vars):
                step = dict(existing_by_id.get(sid, {"step_id": sid}))
                step["skippable"] = skip_v.get()
                step["refine"]    = refine_v.get()
                merged_steps.append(step)
            if merged_steps:
                existing["review_steps"] = merged_steps

            with open(review_config_path, "w", encoding="utf-8") as fh:
                json.dump(existing, fh, indent=2, ensure_ascii=False)
        except Exception as e:
            errors.append(f"review_config.json: {e}")

        if errors:
            messagebox.showerror("Save failed", "\n".join(errors))
        else:
            messagebox.showinfo("Saved", "Settings saved successfully.")
            self.root.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    app  = ConfigApp(root)
    root.mainloop()
