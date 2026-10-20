#!/usr/bin/env python3
"""Settings window — four styled tabs:
  • Voice Refiner  — Whisper / Ollama / audio / storage / ASR profile settings
  • Evening Review — vault paths, review behaviour, TTS models, per-step toggles
  • Notifications  — Telegram alerts, morning brief, voice control, reminder
  • Features       — modular feature toggles
"""
import os
import json
import datetime
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

import requests
import utils
import review_engine
from theme import (
    BG, SURFACE, OVERLAY, FIELD, BORDER, TEXT, SUBTLE, MUTED,
    ACCENT, PRIMARY, PRIMARY_HOVER, GREEN, RED, YELLOW
)

ERROR = RED  # alias used in this file

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

# ── UI Construction Helpers ───────────────────────────────────────────────────

def _card(parent, title, subtitle=None):
    """Creates a rounded container card with styled header."""
    card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
    card.pack(fill="x", padx=16, pady=8)
    card.columnconfigure(1, weight=1)

    hdr = ctk.CTkFrame(card, fg_color="transparent")
    hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 6))

    ctk.CTkLabel(hdr, text=title, font=("Inter", 13, "bold"), text_color=ACCENT).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(hdr, text=subtitle, font=("Inter", 11), text_color=MUTED, wraplength=560, justify="left").pack(anchor="w", pady=(2, 0))
    return card

def _entry(parent, var=None, width=280, placeholder_text=None, **kwargs):
    kwargs.setdefault("fg_color", FIELD)
    kwargs.setdefault("border_color", BORDER)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("corner_radius", 8)
    kwargs.setdefault("text_color", TEXT)
    if var is not None:
        kwargs["textvariable"] = var
    if placeholder_text is not None:
        kwargs["placeholder_text"] = placeholder_text
    return ctk.CTkEntry(parent, width=width, **kwargs)

def _combobox(parent, var=None, values=None, width=280, command=None, **kwargs):
    kwargs.setdefault("fg_color", FIELD)
    kwargs.setdefault("border_color", BORDER)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("corner_radius", 8)
    kwargs.setdefault("text_color", TEXT)
    kwargs.setdefault("button_color", OVERLAY)
    kwargs.setdefault("button_hover_color", BORDER)
    kwargs.setdefault("dropdown_fg_color", SURFACE)
    kwargs.setdefault("dropdown_text_color", TEXT)
    kwargs.setdefault("dropdown_hover_color", OVERLAY)
    if var is not None:
        kwargs["variable"] = var
    if values is not None:
        kwargs["values"] = values
    if command is not None:
        kwargs["command"] = command
    return ctk.CTkComboBox(parent, width=width, **kwargs)

def _row(card, label_text, widget, row, note_text=None):
    ctk.CTkLabel(card, text=label_text, text_color=TEXT, font=("Inter", 12)).grid(
        row=row, column=0, sticky="w", padx=16, pady=4)
    widget.grid(row=row, column=1, sticky="we", padx=16, pady=4)
    if note_text:
        row += 1
        note_lbl = ctk.CTkLabel(card, text=note_text, text_color=MUTED, font=("Inter", 10), wraplength=520, justify="left")
        note_lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 6))
        return note_lbl, row
    return None, row

_FEATURE_ROWS = [
    ("start_end_sounds", "🔔  Start / End Sounds",
     "Play audio cues when recording starts and stops."),
    ("clipboard_output", "📋  Clipboard Output",
     "Copy refined text to clipboard after processing."),
    ("markdown_output",  "📝  Markdown Output",
     "Also save refined text to the Markdown notes file."),
    ("direct_typing",    "⌨   Direct Typing",
     "Type refined text directly at the cursor position (pynput)."),
    ("evening_review",   "🌙  Evening Review",
     "Show 'Start Evening Review' in the tray menu. Disable to use Voice Refiner only."),
    ("pwd_terminology_corrector", "🏛  PWD Terminology Corrector",
     "Auto-capitalizes and normalizes PWD abbreviations (NIT, MB, EE, RCC, SOR) in voice transcripts."),
]

# ── Main application ───────────────────────────────────────────────────────────

class FastScrollableFrame(ctk.CTkFrame):
    """Ultra-fast, lightweight scrollable frame replacing sluggish CTkScrollableFrame.
    Reduces tab load times from 20s down to ~1.3s on Linux X11/Wayland.
    """
    def __init__(self, parent, fg_color="transparent", **kwargs):
        super().__init__(parent, fg_color=fg_color, **kwargs)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ctk.CTkFrame(self.canvas, fg_color=fg_color)
        self._window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._window_id, width=e.width))

        for w in (self, self.canvas, self.content):
            w.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))
            w.bind("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))
            w.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))


class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant — Settings")
        self.root.geometry("720x820")
        self.root.minsize(660, 620)
        self.root.configure(fg_color=BG)

        self.main_cfg   = load_main_config()
        self.review_raw = load_review_config_raw()

        self._cached_ollama_models = []
        self._cached_review_models = []
        self._built_tabs = set()

        self._init_all_variables()
        self._build_ui()
        self._load_ollama_models()

    def _init_all_variables(self):
        # 1. Main / Voice Refiner Config Variables
        profiles = list(self.main_cfg.get("MODEL_PROFILES", {}).keys())
        if not profiles:
            profiles = ["nemotron_fast", "whisper_large_v3", "whisper_turbo", "hinglish_apex"]
        self.asr_profile_var = ctk.StringVar(value=self.main_cfg.get("ACTIVE_MODEL_PROFILE", profiles[0]))
        self.asr_engine_var = ctk.StringVar(value=self.main_cfg.get("ASR_ENGINE", "transcribe_cpp"))
        self.whisper_var = ctk.StringVar(value=self.main_cfg.get("WHISPER_MODEL", "large-v3-turbo"))
        self.en_model_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_MODELS", {}).get("en", ""))
        self.hi_model_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_MODELS", {}).get("hi", ""))
        self.to_en_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_en", ""))
        self.to_hi_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_hi", ""))
        self.host_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_HOST", "http://localhost:11434"))

        cur_ka = str(self.main_cfg.get("OLLAMA_KEEP_ALIVE", "60m")).strip()
        ka_map = {
            "0": "0 (Immediate unload — Low VRAM)",
            "2m": "2m",
            "5m": "5m (Default)",
            "15m": "15m",
            "60m": "60m (Work session)",
            "-1": "-1 (Keep resident in VRAM)",
        }
        self.ollama_keep_alive_var = ctk.StringVar(value=ka_map.get(cur_ka, cur_ka))
        self.threshold_var = ctk.IntVar(value=self.main_cfg.get("SILENCE_THRESHOLD", 300))
        self.silence_dur_var = ctk.DoubleVar(value=self.main_cfg.get("SILENCE_DURATION", 2.0))
        self.temp_var = ctk.DoubleVar(value=self.main_cfg.get("TEMPERATURE", 0.1))
        self.mode_var = ctk.StringVar(value=self.main_cfg.get("MODE", "refine"))
        self.lang_mode_var = ctk.StringVar(value=self.main_cfg.get("LANGUAGE_MODE", "bilingual"))
        self.save_md_var = tk.BooleanVar(value=self.main_cfg.get("SAVE_TO_MARKDOWN", False))
        self.md_path_var = ctk.StringVar(value=self.main_cfg.get("MARKDOWN_PATH", "~/voice_notes.md"))
        self.direct_typing_var = tk.BooleanVar(value=self.main_cfg.get("DIRECT_TYPING", True))

        # 2. Features Tab Variables
        features = self.main_cfg.get("FEATURES", {})
        self._feature_vars = {}
        for key, _, _ in _FEATURE_ROWS:
            self._feature_vars[key] = tk.BooleanVar(value=features.get(key, True))

        # 3. Evening Review Tab Variables
        vp = self.review_raw.get("vault_paths", {})
        self.vault_base_var = ctk.StringVar(value=vp.get("base_vault", "~/learning_vault"))
        self.vault_daily_var = ctk.StringVar(value=vp.get("daily_notes", "~/learning_vault/My Daily Notes"))
        self.vault_well_var = ctk.StringVar(value=vp.get("wellness_notes", "~/learning_vault/04_Wellness_and_Journal"))
        self.expiry_var = ctk.StringVar(value=str(self.review_raw.get("review_expiry_hours", 1)))
        self.narration_var = tk.BooleanVar(value=self.review_raw.get("voice_narration", True))
        self.context_days_var = ctk.StringVar(value=str(self.review_raw.get("last_n_days_context", 3)))
        self.per_step_ctx_var = tk.BooleanVar(value=self.review_raw.get("per_step_context", True))
        self.carryforward_var = tk.BooleanVar(value=self.review_raw.get("carryforward_tasks", True))
        self.carryforward_step_var = ctk.StringVar(value=str(self.review_raw.get("carryforward_step_id", 3)))
        self.tts_engine_var = ctk.StringVar(value=self.review_raw.get("tts_engine", "piper"))
        self.piper_model_var = ctk.StringVar(value=self.review_raw.get("piper_model", "models/en_US-lessac-medium.onnx"))
        self.piper_model_hi_var = ctk.StringVar(value=self.review_raw.get("piper_model_hi", "models/hi_IN-priyamvada-medium.onnx"))
        self.brief_lang_var = ctk.StringVar(value=self.review_raw.get("context_brief_language", "source"))

        mode_val = "Two Models (EN + HI)" if (self.review_raw.get("brief_model_en") or self.review_raw.get("brief_model_hi")) else "Single Model"
        self.brief_mode_var = ctk.StringVar(value=mode_val)
        self.brief_model_var = ctk.StringVar(value=self.review_raw.get("brief_model", ""))
        self.brief_model_en_var = ctk.StringVar(value=self.review_raw.get("brief_model_en", ""))
        self.brief_model_hi_var = ctk.StringVar(value=self.review_raw.get("brief_model_hi", ""))
        self.secretary_model_var = ctk.StringVar(value=self.review_raw.get("secretary_model", ""))
        self.review_host_var = ctk.StringVar(value=self.review_raw.get("ollama_host", "http://localhost:11434"))
        self.struct_model_var = ctk.StringVar(value=self.review_raw.get("structure_model", ""))

        steps = self.review_raw.get("review_steps", [])
        self._step_ids = [s["step_id"] for s in steps if "step_id" in s]
        self.step_skippable_vars = [tk.BooleanVar(value=s.get("skippable", True)) for s in steps if "step_id" in s]
        self.step_refine_vars = [tk.BooleanVar(value=s.get("refine", True)) for s in steps if "step_id" in s]

        self.voice_ctrl_var = tk.BooleanVar(value=self.review_raw.get("voice_control", False))
        self.voice_threshold_var = ctk.StringVar(value=str(self.review_raw.get("voice_control_threshold", 500)))
        self.evening_reminder_var = tk.BooleanVar(value=self.review_raw.get("evening_reminder_enabled", False))
        self.evening_reminder_time_var = ctk.StringVar(value=self.review_raw.get("evening_reminder_time", "21:00"))

        # 4. Notifications Tab Variables
        self.tg_enabled_var = tk.BooleanVar(value=self.review_raw.get("telegram_enabled", False))
        self.tg_token_var = ctk.StringVar(value=self.review_raw.get("telegram_bot_token", ""))
        self.tg_chat_var = ctk.StringVar(value=self.review_raw.get("telegram_chat_id", ""))
        self.morning_enabled_var = tk.BooleanVar(value=self.review_raw.get("morning_briefing_enabled", False))
        self.morning_time_var = ctk.StringVar(value=self.review_raw.get("morning_briefing_time", "08:00"))
        self.pending_lookback_var = ctk.StringVar(value=str(self.review_raw.get("pending_task_lookback_days", 7)))
        self.pending_warn_var = ctk.StringVar(value=str(self.review_raw.get("pending_task_warn_threshold", 3)))
        self.pending_crit_var = ctk.StringVar(value=str(self.review_raw.get("pending_task_critical_threshold", 5)))

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(
            self.root, fg_color="transparent",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=PRIMARY_HOVER,
            segmented_button_unselected_color=SURFACE,
            segmented_button_unselected_hover_color=OVERLAY,
            command=self._on_tab_change
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(10, 10))

        self.tab1 = self.tabview.add("Voice Refiner")
        self.tab2 = self.tabview.add("Evening Review")
        self.tab3 = self.tabview.add("Notifications")
        self.tab4 = self.tabview.add("Features")

        # Build initial active tab immediately
        self._ensure_tab_built("Voice Refiner")

    def _on_tab_change(self):
        tab_name = self.tabview.get()
        self._ensure_tab_built(tab_name)

    def _ensure_tab_built(self, tab_name: str):
        if tab_name in self._built_tabs:
            return
        self._built_tabs.add(tab_name)

        if tab_name == "Voice Refiner":
            self.scroll1 = FastScrollableFrame(self.tab1)
            self.scroll1.pack(fill="both", expand=True)
            self._build_voice_tab(self.scroll1.content)
            if self._cached_ollama_models:
                self._populate_model_dropdowns(self._cached_ollama_models)
        elif tab_name == "Evening Review":
            self.scroll2 = FastScrollableFrame(self.tab2)
            self.scroll2.pack(fill="both", expand=True)
            self._build_review_tab(self.scroll2.content)
            if self._cached_review_models:
                self._populate_review_dropdowns(self._cached_review_models)
            else:
                self._load_review_ollama_models()
        elif tab_name == "Notifications":
            self.scroll3 = FastScrollableFrame(self.tab3)
            self.scroll3.pack(fill="both", expand=True)
            self._build_notifications_tab(self.scroll3.content)
        elif tab_name == "Features":
            self.scroll4 = FastScrollableFrame(self.tab4)
            self.scroll4.pack(fill="both", expand=True)
            self._build_features_tab(self.scroll4.content)

        # Save / Cancel bottom bar
        bar = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
        bar.pack(fill="x", side="bottom", pady=(4, 16), padx=16)

        ctk.CTkButton(
            bar, text="💾 Save All Settings", command=self._save_all,
            fg_color=ACCENT, text_color=BG, font=("Inter", 13, "bold"),
            hover_color=PRIMARY_HOVER, corner_radius=8, height=38
        ).pack(side=ctk.LEFT, padx=12, pady=10)

        ctk.CTkButton(
            bar, text="✕ Cancel", command=self.root.destroy,
            fg_color=FIELD, text_color=TEXT, font=("Inter", 13),
            hover_color=OVERLAY, border_color=BORDER, border_width=1,
            corner_radius=8, height=38
        ).pack(side=ctk.LEFT, padx=(0, 10), pady=10)

        ctk.CTkButton(
            bar, text="📖 User Manual", command=self._open_user_manual,
            fg_color=FIELD, text_color=ACCENT, font=("Inter", 13, "bold"),
            hover_color=OVERLAY, border_color=BORDER, border_width=1,
            corner_radius=8, height=38
        ).pack(side=ctk.LEFT, padx=(0, 10), pady=10)

        active_prof = self.main_cfg.get("ACTIVE_MODEL_PROFILE", "default")
        ctk.CTkLabel(
            bar, text=f"Active Profile: {active_prof}", font=("Inter", 11, "bold"),
            text_color=MUTED
        ).pack(side=ctk.RIGHT, padx=16, pady=10)

    def _open_user_manual(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.Popen([sys.executable, os.path.join(script_dir, "manual_gui.py")])

    def _build_voice_tab(self, f):
        # 1. Speech-to-Text (ASR) Card
        asr_card = _card(f, "🎙  Speech-to-Text (ASR)", "Choose speech engine and active model profile.")
        
        profiles = list(self.main_cfg.get("MODEL_PROFILES", {}).keys())
        if not profiles:
            profiles = ["nemotron_fast", "whisper_large_v3", "whisper_turbo", "hinglish_apex"]
        self.asr_profile_var = ctk.StringVar(value=self.main_cfg.get("ACTIVE_MODEL_PROFILE", profiles[0]))
        self.asr_profile_cb = _combobox(asr_card, var=self.asr_profile_var, values=profiles)
        _row(asr_card, "ASR Model Profile:", self.asr_profile_cb, 1,
             "High-level profile selecting backend, weights, and precision.")

        engine_val = self.main_cfg.get("ASR_ENGINE", "transcribe_cpp")
        self.asr_engine_var = ctk.StringVar(value=engine_val)
        asr_eng_cb = _combobox(asr_card, var=self.asr_engine_var, values=["transcribe_cpp", "faster_whisper", "handy_cli"])
        _row(asr_card, "ASR Engine Backend:", asr_eng_cb, 3,
             "transcribe_cpp (Vulkan/CUDA GGUF), faster_whisper (CTranslate2), or handy_cli.")

        try:
            from audio_to_idea.asr import TranscribeCppProvider
            tcpp_ok = TranscribeCppProvider.is_available()
        except Exception:
            tcpp_ok = False
        if not tcpp_ok:
            ctk.CTkLabel(asr_card, text="⚠️ transcribe-cpp is not available in environment; pip install transcribe-cpp",
                         text_color=YELLOW, font=("Inter", 10)).grid(row=5, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 4))

        self.whisper_var = ctk.StringVar(value=self.main_cfg.get("WHISPER_MODEL", "large-v3-turbo"))
        whisp_cb = _combobox(asr_card, var=self.whisper_var, values=["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"])
        _row(asr_card, "Whisper Fallback Model:", whisp_cb, 6, "Fallback model when using faster_whisper backend.")

        # 2. Refinement Models Card
        ref_card = _card(f, "✨  Refinement Models", "Local Ollama models that correct grammar and remove fillers.")
        self.en_model_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_MODELS", {}).get("en", ""))
        self.en_cb = _combobox(ref_card, var=self.en_model_var)
        _row(ref_card, "English Refiner:", self.en_cb, 1, "Model used for English audio refinement (e.g. qwen2.5:3b).")

        self.hi_model_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_MODELS", {}).get("hi", ""))
        self.hi_cb = _combobox(ref_card, var=self.hi_model_var)
        _row(ref_card, "Hindi Refiner:", self.hi_cb, 3, "Model used for Hindi audio refinement.")

        # 3. Translation Models Card
        trans_card = _card(f, "🌍  Translation Models", "Local Ollama models for bidirectional language translation.")
        self.to_en_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_en", ""))
        self.to_en_cb = _combobox(trans_card, var=self.to_en_var)
        _row(trans_card, "→ English Translation:", self.to_en_cb, 1)

        self.to_hi_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_hi", ""))
        self.to_hi_cb = _combobox(trans_card, var=self.to_hi_var)
        _row(trans_card, "→ Hindi Translation:", self.to_hi_cb, 2)

        # 4. AI Parameters & Memory Lifecycle Card
        ai_card = _card(f, "⚙️  AI Parameters & VRAM Lifecycle", "Configure Ollama connection, keep-alive duration, and sampling temperature.")
        self.host_var = ctk.StringVar(value=self.main_cfg.get("OLLAMA_HOST", "http://localhost:11434"))
        host_entry = _entry(ai_card, var=self.host_var)
        _row(ai_card, "Ollama Host:", host_entry, 1)
        self.host_var.trace_add("write", lambda *_: self._load_ollama_models())

        cur_ka = str(self.main_cfg.get("OLLAMA_KEEP_ALIVE", "60m")).strip()
        ka_map = {
            "0": "0 (Immediate unload — Low VRAM)",
            "2m": "2m",
            "5m": "5m (Default)",
            "15m": "15m",
            "60m": "60m (Work session)",
            "-1": "-1 (Keep resident in VRAM)",
        }
        initial_ka = ka_map.get(cur_ka, cur_ka)
        self.ollama_keep_alive_var = ctk.StringVar(value=initial_ka)
        ka_cb = _combobox(ai_card, var=self.ollama_keep_alive_var, values=list(ka_map.values()))
        _row(ai_card, "Ollama Keep-Alive:", ka_cb, 2,
             "How long Ollama keeps model weights in GPU VRAM. Set 0 to offload immediately on low-memory systems.")

        self.temp_var = ctk.DoubleVar(value=self.main_cfg.get("TEMPERATURE", 0.1))
        temp_entry = _entry(ai_card, var=self.temp_var)
        _row(ai_card, "Sampling Temperature:", temp_entry, 4)

        self.lang_mode_var = ctk.StringVar(value=self.main_cfg.get("LANGUAGE_MODE", "bilingual"))
        lang_mode_cb = _combobox(ai_card, var=self.lang_mode_var, values=["bilingual", "pure_english", "pure_hindi", "roman_hinglish"])
        _row(ai_card, "Language & Output Style:", lang_mode_cb, 5,
             "bilingual: Natural mixed Hinglish (default) | pure_english: Full English translation | pure_hindi: Formal Hindi with tech terms in EN | roman_hinglish: Latin alphabet everywhere.")

        self.mode_var = ctk.StringVar(value=self.main_cfg.get("MODE", "refine"))
        mode_cb = _combobox(ai_card, var=self.mode_var, values=["refine", "translate"])
        _row(ai_card, "Legacy Processing Mode:", mode_cb, 6)

        # 5. Audio Settings Card
        audio_card = _card(f, "🔉  Audio Settings", "Silence detection thresholds and recording duration.")
        self.threshold_var = ctk.IntVar(value=self.main_cfg.get("SILENCE_THRESHOLD", 300))
        slider = ctk.CTkSlider(audio_card, from_=50, to=1000, variable=self.threshold_var, button_color=ACCENT, progress_color=ACCENT)
        _row(audio_card, "Silence Threshold:", slider, 1, "Energy cutoff below which audio is treated as silence.")

        self.silence_dur_var = ctk.DoubleVar(value=self.main_cfg.get("SILENCE_DURATION", 2.0))
        dur_entry = _entry(audio_card, var=self.silence_dur_var)
        _row(audio_card, "Silence Duration (s):", dur_entry, 3, "Seconds of continuous silence before auto-stopping.")

        # 6. Storage & Output Card
        store_card = _card(f, "📁  Storage & Output", "Configure destination and automatic text typing.")
        self.save_md_var = tk.BooleanVar(value=self.main_cfg.get("SAVE_TO_MARKDOWN", False))
        md_sw = ctk.CTkSwitch(store_card, text="", variable=self.save_md_var, button_color=ACCENT, progress_color=ACCENT)
        _row(store_card, "Save to Markdown:", md_sw, 1)

        self.md_path_var = ctk.StringVar(value=self.main_cfg.get("MARKDOWN_PATH", "~/Documents/VoiceNotes"))
        md_entry = _entry(store_card, var=self.md_path_var)
        _row(store_card, "Markdown Path:", md_entry, 2)

        self.direct_typing_var = tk.BooleanVar(value=self.main_cfg.get("DIRECT_TYPING", False))
        type_sw = ctk.CTkSwitch(store_card, text="", variable=self.direct_typing_var, button_color=ACCENT, progress_color=ACCENT)
        _row(store_card, "Direct Typing:", type_sw, 3, "Types refined text directly at active cursor position (pynput).")

    def _build_review_tab(self, f):
        vp = self.review_raw.get("vault_paths", {})

        # 1. Obsidian Vault Paths Card
        vault_card = _card(f, "📂  Obsidian Vault Paths", "Use ~ for home directory. Folders are created automatically.")
        self.vault_base_var = ctk.StringVar(value=vp.get("base_vault", "~/learning_vault"))
        _row(vault_card, "Base Vault:", _entry(vault_card, var=self.vault_base_var), 1)

        self.vault_daily_var = ctk.StringVar(value=vp.get("daily_notes", "~/learning_vault/My Daily Notes"))
        _row(vault_card, "Daily Notes:", _entry(vault_card, var=self.vault_daily_var), 2)

        self.vault_well_var = ctk.StringVar(value=vp.get("wellness_notes", "~/learning_vault/My Daily Notes/Wellness"))
        _row(vault_card, "Wellness Notes:", _entry(vault_card, var=self.vault_well_var), 3)

        # 2. Review Behaviour Card
        behav_card = _card(f, "⚙️  Review Behaviour", "Configure expiry, narration prompts, and carry-forward tasks.")
        self.expiry_var = ctk.StringVar(value=str(self.review_raw.get("review_expiry_hours", 1)))
        _row(behav_card, "Session Expiry (hours):", _combobox(behav_card, var=self.expiry_var, values=["1","2","3","4","5","6","7","8"], width=120), 1,
             "Review state expires after this many hours of inactivity.")

        self.narration_var = tk.BooleanVar(value=self.review_raw.get("voice_narration", True))
        _row(behav_card, "Voice Narration:", ctk.CTkSwitch(behav_card, text="", variable=self.narration_var, button_color=ACCENT, progress_color=ACCENT), 3,
             "Speak step prompts aloud when each review step begins.")

        self.context_days_var = ctk.StringVar(value=str(self.review_raw.get("last_n_days_context", 3)))
        _row(behav_card, "Context Days:", _combobox(behav_card, var=self.context_days_var, values=["0","1","2","3","4","5","6","7"], width=120), 5,
             "Days of past notes read at review start. Set 0 to disable.")

        self.per_step_ctx_var = tk.BooleanVar(value=self.review_raw.get("per_step_context", False))
        _row(behav_card, "Per-step Context:", ctk.CTkSwitch(behav_card, text="", variable=self.per_step_ctx_var, button_color=ACCENT, progress_color=ACCENT), 7,
             "Show step-relevant history in the context panel as each step starts.")

        self.carryforward_var = tk.BooleanVar(value=self.review_raw.get("carryforward_tasks", True))
        _row(behav_card, "Carry-forward Tasks:", ctk.CTkSwitch(behav_card, text="", variable=self.carryforward_var, button_color=ACCENT, progress_color=ACCENT), 9,
             "Read unchecked tasks from yesterday's Priorities and show them at the carry-forward step.")

        self.carryforward_step_var = ctk.StringVar(value=str(self.review_raw.get("carryforward_step_id", 3)))
        _row(behav_card, "Carry-forward Step:", _combobox(behav_card, var=self.carryforward_step_var, values=["1", "2", "3", "4", "5", "6"], width=120), 11,
             "Which step shows the carry-forward task checklist (default: 3).")

        # 3. Text-to-Speech (Step Narration) Card
        tts_card = _card(f, "🔊  Text-to-Speech (Step Narration)", "Engine used to narrate step prompts. Piper sounds natural; espeak is the fallback.")
        self.tts_engine_var = ctk.StringVar(value=self.review_raw.get("tts_engine", "espeak"))
        tts_cb = _combobox(tts_card, var=self.tts_engine_var, values=["espeak", "piper"], width=140, command=self._on_tts_engine_change)
        _row(tts_card, "TTS Engine:", tts_cb, 1, "espeak: built-in, no setup needed.  piper: neural voice, requires model file.")

        self.piper_model_var = ctk.StringVar(value=self.review_raw.get("piper_model", ""))
        self.piper_model_entry = _entry(tts_card, var=self.piper_model_var, placeholder_text="e.g. ~/models/en_US-ryan-high.onnx")
        self.piper_model_entry.grid(row=3, column=1, sticky="we", padx=16, pady=4)
        ctk.CTkLabel(tts_card, text="Piper Model (EN):", text_color=TEXT, font=("Inter", 12)).grid(row=3, column=0, sticky="w", padx=16, pady=4)
        self._piper_note = ctk.CTkLabel(tts_card, text="English .onnx model. Matching .onnx.json must be in same folder.", text_color=MUTED, font=("Inter", 10), wraplength=480, justify="left")
        self._piper_note.grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 6))

        self.piper_model_hi_var = ctk.StringVar(value=self.review_raw.get("piper_model_hi", ""))
        self.piper_model_hi_entry = _entry(tts_card, var=self.piper_model_hi_var, placeholder_text="e.g. ~/models/hi_IN-dhvani-medium.onnx")
        self.piper_model_hi_entry.grid(row=5, column=1, sticky="we", padx=16, pady=4)
        ctk.CTkLabel(tts_card, text="Piper Model (HI):", text_color=TEXT, font=("Inter", 12)).grid(row=5, column=0, sticky="w", padx=16, pady=4)
        self._piper_hi_note = ctk.CTkLabel(tts_card, text="Hindi .onnx model. Used when narration text contains Devanagari.", text_color=MUTED, font=("Inter", 10), wraplength=480, justify="left")
        self._piper_hi_note.grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 6))

        self._on_tts_engine_change(self.tts_engine_var.get())

        # 4. AI Models for Review Card
        rev_m_card = _card(f, "🤖  AI Models for Review", "Secretary model synthesizes your review; Context brief model analyzes past notes.")
        self.secretary_model_var = ctk.StringVar(value=self.review_raw.get("secretary_model", ""))
        self.secretary_cb = _combobox(rev_m_card, var=self.secretary_model_var)
        _row(rev_m_card, "Secretary Model:", self.secretary_cb, 1, "Organises answers into note sections after review (e.g. qwen2.5:3b).")

        self.struct_model_var = ctk.StringVar(value=self.review_raw.get("structure_model", ""))
        self.struct_cb = _combobox(rev_m_card, var=self.struct_model_var)
        _row(rev_m_card, "Context Brief Model:", self.struct_cb, 3, "Generates AI context brief from past notes. Blank inherits default.")

        self.review_host_var = ctk.StringVar(value=self.review_raw.get("ollama_host", "http://localhost:11434"))
        rev_host_entry = _entry(rev_m_card, var=self.review_host_var, placeholder_text="http://localhost:11434")
        _row(rev_m_card, "Ollama Host (Review):", rev_host_entry, 5)
        self.review_host_var.trace_add("write", lambda *_: self._load_review_ollama_models())

        # 5. Context Brief Card
        brief_card = _card(f, "🌐  Context Brief", "Nightly context brief language and model selection.")
        self.brief_lang_var = ctk.StringVar(value=self.review_raw.get("context_brief_language", "en"))
        _row(brief_card, "Brief Language:", _combobox(brief_card, var=self.brief_lang_var, values=["en", "hi"], width=120), 1)

        _has_two = bool(self.review_raw.get("brief_model_en") or self.review_raw.get("brief_model_hi"))
        self.brief_mode_var = ctk.StringVar(value="Two Models" if _has_two else "Single Model")
        brief_mode_cb = _combobox(brief_card, var=self.brief_mode_var, values=["Single Model", "Two Models"], width=150, command=self._on_brief_mode_change)
        _row(brief_card, "Brief Mode:", brief_mode_cb, 2)
        self._brief_mode_note = ctk.CTkLabel(brief_card, text="Single Model: one call returns both languages. Two Models: parallel per-language calls.", text_color=MUTED, font=("Inter", 10), wraplength=480, justify="left")
        self._brief_mode_note.grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 6))

        self.brief_model_var = ctk.StringVar(value=self.review_raw.get("brief_model", ""))
        self.brief_model_entry = _entry(brief_card, var=self.brief_model_var, placeholder_text="e.g. qwen2.5:7b (blank = structure model)")
        _row(brief_card, "Brief Model:", self.brief_model_entry, 4)

        self.brief_model_en_var = ctk.StringVar(value=self.review_raw.get("brief_model_en", ""))
        self.brief_model_en_entry = _entry(brief_card, var=self.brief_model_en_var, placeholder_text="e.g. qwen2.5:7b")
        _row(brief_card, "Brief Model (EN):", self.brief_model_en_entry, 5)

        self.brief_model_hi_var = ctk.StringVar(value=self.review_raw.get("brief_model_hi", ""))
        self.brief_model_hi_entry = _entry(brief_card, var=self.brief_model_hi_var, placeholder_text="e.g. aya-expanse:8b")
        _row(brief_card, "Brief Model (HI):", self.brief_model_hi_entry, 6)

        self._on_brief_mode_change(self.brief_mode_var.get())

        # 6. Step Configuration Card
        steps_card = _card(f, "📋  Step Configuration", "Toggle per-step skippability and AI refinement.")
        hdr = ctk.CTkFrame(steps_card, fg_color=FIELD, corner_radius=6, border_width=1, border_color=BORDER)
        hdr.grid(row=1, column=0, columnspan=2, sticky="we", padx=16, pady=(6, 4))
        for col_text, col_w in [("Step", 200), ("Skippable", 100), ("AI Refine", 100)]:
            ctk.CTkLabel(hdr, text=col_text, text_color=ACCENT, font=("Inter", 11, "bold"), width=col_w, anchor="w").pack(side=ctk.LEFT, padx=10, pady=6)

        full_cfg = review_engine.load_review_config(script_dir)
        self.step_skippable_vars = []
        self.step_refine_vars    = []
        self._step_ids           = []

        for row_i, step in enumerate(full_cfg.get("review_steps", [])):
            row_frame = ctk.CTkFrame(steps_card, fg_color="transparent")
            row_frame.grid(row=2 + row_i, column=0, columnspan=2, sticky="we", padx=16, pady=2)

            ctk.CTkLabel(row_frame, text=f"{step['step_id']}. {step['section_name']}",
                         text_color=TEXT, font=("Inter", 12), width=200, anchor="w").pack(side=ctk.LEFT, padx=(10, 0), pady=4)

            skip_var = tk.BooleanVar(value=step.get("skippable", True))
            ctk.CTkSwitch(row_frame, text="", variable=skip_var, width=100, button_color=ACCENT, progress_color=ACCENT).pack(side=ctk.LEFT, padx=(20, 0))

            refine_var = tk.BooleanVar(value=step.get("refine", True))
            ctk.CTkSwitch(row_frame, text="", variable=refine_var, width=100, button_color=ACCENT, progress_color=ACCENT).pack(side=ctk.LEFT, padx=(20, 0))

            self.step_skippable_vars.append(skip_var)
            self.step_refine_vars.append(refine_var)
            self._step_ids.append(step["step_id"])

    def _build_notifications_tab(self, f):
        # 1. Telegram Card
        tg_card = _card(f, "📲  Telegram", "Send key events (morning brief, review complete) to your phone.")
        self.tg_enabled_var = tk.BooleanVar(value=self.review_raw.get("telegram_enabled", False))
        _row(tg_card, "Enable Telegram:", ctk.CTkSwitch(tg_card, text="", variable=self.tg_enabled_var, button_color=ACCENT, progress_color=ACCENT), 1)

        self.tg_token_var = ctk.StringVar(value=self.review_raw.get("telegram_bot_token", ""))
        _row(tg_card, "Bot Token:", _entry(tg_card, var=self.tg_token_var, placeholder_text="From @BotFather — keep private"), 2)

        self.tg_chat_var = ctk.StringVar(value=self.review_raw.get("telegram_chat_id", ""))
        _row(tg_card, "Chat ID:", _entry(tg_card, var=self.tg_chat_var, placeholder_text="e.g. 59509781"), 3,
             "To find your chat ID: message your bot once, then open https://api.telegram.org/bot<TOKEN>/getUpdates")

        self.tg_test_btn = ctk.CTkButton(
            tg_card, text="Send Test Message", width=180, height=32,
            fg_color=ACCENT, text_color=BG, hover_color=PRIMARY_HOVER,
            font=("Inter", 12, "bold"), corner_radius=8,
            command=lambda: threading.Thread(target=self._test_telegram, daemon=True).start()
        )
        self.tg_test_btn.grid(row=5, column=1, sticky="w", padx=16, pady=(6, 4))

        self.tg_status_lbl = ctk.CTkLabel(tg_card, text="", text_color=MUTED, font=("Inter", 11))
        self.tg_status_lbl.grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 6))

        # 2. Morning Brief Card
        morn_card = _card(f, "🌅  Morning Brief Notifications", "Sends your Tomorrow's Priorities to Telegram each morning.")
        self.morning_enabled_var = tk.BooleanVar(value=self.review_raw.get("morning_briefing_enabled", False))
        _row(morn_card, "Enable Morning Brief:", ctk.CTkSwitch(morn_card, text="", variable=self.morning_enabled_var, button_color=ACCENT, progress_color=ACCENT), 1)

        self.morning_time_var = ctk.StringVar(value=self.review_raw.get("morning_briefing_time", "08:00"))
        _row(morn_card, "Brief Time (HH:MM):", _entry(morn_card, var=self.morning_time_var, width=120, placeholder_text="08:00"), 2,
             "After changing the time, re-run install_morning_brief.sh to update the systemd timer.")

        self.pending_lookback_var = ctk.StringVar(value=str(self.review_raw.get("pending_task_lookback_days", 7)))
        _row(morn_card, "Pending Lookback Days:", _entry(morn_card, var=self.pending_lookback_var, width=100), 4)

        self.pending_warn_var = ctk.StringVar(value=str(self.review_raw.get("pending_task_warn_threshold", 3)))
        _row(morn_card, "Warn Threshold (days):", _entry(morn_card, var=self.pending_warn_var, width=100), 5)

        self.pending_crit_var = ctk.StringVar(value=str(self.review_raw.get("pending_task_critical_threshold", 5)))
        _row(morn_card, "Critical Threshold (days):", _entry(morn_card, var=self.pending_crit_var, width=100), 6)

        # 3. Voice Wake-Word Control Card
        voice_card = _card(f, "🎙  Voice Wake-Word Control", "Hands-free voice keywords: 'stop', 'again', 'next', 'skip', 'back'. Active only during TTS.")
        self.voice_ctrl_var = tk.BooleanVar(value=self.review_raw.get("voice_control", False))
        _row(voice_card, "Enable Voice Control:", ctk.CTkSwitch(voice_card, text="", variable=self.voice_ctrl_var, button_color=ACCENT, progress_color=ACCENT), 1)

        self.voice_threshold_var = ctk.StringVar(value=str(self.review_raw.get("voice_control_threshold", 500)))
        _row(voice_card, "Energy Threshold:", _entry(voice_card, var=self.voice_threshold_var, width=120), 2,
             "RMS energy gate (0–32768). Raise if speaker bleed triggers false positives.")

        # 4. Evening Review Reminder Card
        rem_card = _card(f, "🌙  Evening Review Reminder", "Sends a desktop alert if no review has been completed by target time.")
        self.evening_reminder_var = tk.BooleanVar(value=self.review_raw.get("evening_reminder_enabled", False))
        _row(rem_card, "Enable Reminder:", ctk.CTkSwitch(rem_card, text="", variable=self.evening_reminder_var, button_color=ACCENT, progress_color=ACCENT), 1)

        self.evening_reminder_time_var = ctk.StringVar(value=self.review_raw.get("evening_reminder_time", "21:00"))
        _row(rem_card, "Reminder Time (HH:MM):", _entry(rem_card, var=self.evening_reminder_time_var, width=120, placeholder_text="21:00"), 2,
             "After changing the time, re-run install_evening_reminder.sh to update the systemd timer.")

    def _build_features_tab(self, f):
        card = _card(f, "⚙  Feature Toggles", "Turn individual features on or off without editing code. Changes take effect on tray restart.")

        features = self.main_cfg.get("FEATURES", {})
        self._feature_vars = {}
        for row_i, (key, label, note) in enumerate(_FEATURE_ROWS):
            row_frame = ctk.CTkFrame(card, fg_color=FIELD, corner_radius=8, border_width=1, border_color=BORDER)
            row_frame.grid(row=1 + row_i, column=0, columnspan=2, sticky="we", padx=16, pady=4)
            row_frame.columnconfigure(0, weight=1)

            var = tk.BooleanVar(value=features.get(key, True))
            self._feature_vars[key] = var

            ctk.CTkLabel(row_frame, text=label, text_color=TEXT, font=("Inter", 12, "bold"), anchor="w").grid(
                row=0, column=0, sticky="w", padx=14, pady=(8, 2))
            ctk.CTkSwitch(row_frame, text="", variable=var,
                          button_color=ACCENT, progress_color=ACCENT).grid(
                row=0, column=1, sticky="e", padx=14, pady=(8, 2))
            ctk.CTkLabel(row_frame, text=note, text_color=MUTED,
                         font=("Inter", 10), anchor="w", wraplength=480).grid(
                row=1, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 8))

    def _test_telegram(self):
        self.root.after(0, lambda: (
            self.tg_test_btn.configure(state="disabled", text="Testing…"),
            self.tg_status_lbl.configure(text="Connecting…", text_color=SUBTLE),
        ))
        try:
            import telegram_service
            config = {
                "telegram_enabled": True,
                "telegram_bot_token": self.tg_token_var.get().strip(),
                "telegram_chat_id":   self.tg_chat_var.get().strip(),
            }
            ok, msg = telegram_service.test_connection(config)
            color = GREEN if ok else ERROR
            self.root.after(0, lambda: self.tg_status_lbl.configure(text=msg, text_color=color))
        except Exception as e:
            self.root.after(0, lambda: self.tg_status_lbl.configure(
                text=f"Error: {e}", text_color=ERROR))
        finally:
            self.root.after(0, lambda: self.tg_test_btn.configure(
                state="normal", text="Send Test Message"))

    def _on_brief_mode_change(self, value):
        """Show single-model field or two-model fields based on selected mode."""
        is_single = value == "Single Model"
        self.brief_model_entry.configure(state="normal" if is_single else "disabled")
        self.brief_model_en_entry.configure(state="disabled" if is_single else "normal")
        self.brief_model_hi_entry.configure(state="disabled" if is_single else "normal")

    def _on_tts_engine_change(self, value):
        """Show/hide piper model paths based on selected engine."""
        is_piper = value == "piper"
        state = "normal" if is_piper else "disabled"
        color = TEXT if is_piper else MUTED
        self.piper_model_entry.configure(state=state)
        self._piper_note.configure(text_color=color)
        self.piper_model_hi_entry.configure(state=state)
        self._piper_hi_note.configure(text_color=color)

    def _load_ollama_models(self, *_):
        host = getattr(self, "host_var", None)
        host_url = host.get() if host else "http://localhost:11434"
        def _fetch():
            try:
                models = get_ollama_models(host_url)
                self._cached_ollama_models = models
                try:
                    self.root.after(0, lambda: self._populate_model_dropdowns(models))
                except Exception:
                    pass
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

    def _load_review_ollama_models(self, *_):
        host = getattr(self, "review_host_var", None)
        host_url = host.get() if host else "http://localhost:11434"
        def _fetch():
            try:
                models = get_ollama_models(host_url)
                self._cached_review_models = models
                try:
                    self.root.after(0, lambda: self._populate_review_dropdowns(models))
                except Exception:
                    pass
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

    def _populate_model_dropdowns(self, models):
        self._cached_ollama_models = models
        for attr in ("en_cb", "hi_cb", "to_en_cb", "to_hi_cb"):
            cb = getattr(self, attr, None)
            if cb:
                try:
                    cb.configure(values=models)
                except Exception:
                    pass

    def _populate_review_dropdowns(self, models):
        self._cached_review_models = models
        if hasattr(self, "secretary_cb") and self.secretary_cb:
            try:
                self.secretary_cb.configure(values=[""] + models)
            except Exception:
                pass
        if hasattr(self, "struct_cb") and self.struct_cb:
            try:
                self.struct_cb.configure(values=[""] + models)
            except Exception:
                pass

    def _save_all(self):
        errors = []
        try:
            raw_ka = self.ollama_keep_alive_var.get().strip()
            if raw_ka.startswith("0"):
                ka = "0"
            elif raw_ka.startswith("-1"):
                ka = "-1"
            elif "5m" in raw_ka:
                ka = "5m"
            elif "60m" in raw_ka:
                ka = "60m"
            elif "15m" in raw_ka:
                ka = "15m"
            elif "2m" in raw_ka:
                ka = "2m"
            else:
                ka = raw_ka.split()[0]

            new_main = dict(self.main_cfg)
            new_main.update({
                "SAMPLE_RATE":              self.main_cfg.get("SAMPLE_RATE", 16000),
                "ASR_ENGINE":               self.asr_engine_var.get(),
                "ACTIVE_MODEL_PROFILE":     self.asr_profile_var.get(),
                "WHISPER_MODEL":            self.whisper_var.get(),
                "OLLAMA_MODELS":            {"en": self.en_model_var.get(), "hi": self.hi_model_var.get()},
                "OLLAMA_TRANSLATE_MODELS":  {"to_en": self.to_en_var.get(), "to_hi": self.to_hi_var.get()},
                "OLLAMA_HOST":              self.host_var.get(),
                "OLLAMA_KEEP_ALIVE":        ka,
                "SILENCE_THRESHOLD":        int(self.threshold_var.get()),
                "SILENCE_DURATION":         float(self.silence_dur_var.get()),
                "TEMPERATURE":              float(self.temp_var.get()),
                "MODE":                     self.mode_var.get(),
                "LANGUAGE_MODE":            self.lang_mode_var.get(),
                "SAVE_TO_MARKDOWN":         self.save_md_var.get(),
                "MARKDOWN_PATH":            self.md_path_var.get(),
                "DIRECT_TYPING":            self.direct_typing_var.get(),
                "FEATURES": {k: v.get() for k, v in self._feature_vars.items()},
            })
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(new_main, fh, indent=4)

            for model_name in set([
                new_main["OLLAMA_MODELS"].get("en", ""),
                new_main["OLLAMA_MODELS"].get("hi", ""),
                new_main["OLLAMA_TRANSLATE_MODELS"].get("to_en", ""),
                new_main["OLLAMA_TRANSLATE_MODELS"].get("to_hi", ""),
            ]):
                if model_name:
                    utils.ensure_model_prompts(script_dir, model_name, new_main)
        except Exception as e:
            errors.append(f"config.json: {e}")

        try:
            existing = load_review_config_raw()

            existing["vault_paths"] = {
                "base_vault":     self.vault_base_var.get().strip(),
                "daily_notes":    self.vault_daily_var.get().strip(),
                "wellness_notes": self.vault_well_var.get().strip(),
            }
            existing["review_expiry_hours"] = int(self.expiry_var.get())
            existing["voice_narration"]     = self.narration_var.get()
            existing["last_n_days_context"] = int(self.context_days_var.get())
            existing["per_step_context"]    = self.per_step_ctx_var.get()
            existing["carryforward_tasks"]  = self.carryforward_var.get()
            existing["carryforward_step_id"] = int(self.carryforward_step_var.get())
            existing["tts_engine"]          = self.tts_engine_var.get()
            existing["piper_model"]         = self.piper_model_var.get().strip()
            existing["piper_model_hi"]      = self.piper_model_hi_var.get().strip()
            existing["context_brief_language"] = self.brief_lang_var.get()
            if self.brief_mode_var.get() == "Single Model":
                existing["brief_model"]    = self.brief_model_var.get().strip()
                existing.pop("brief_model_en", None)
                existing.pop("brief_model_hi", None)
            else:
                existing.pop("brief_model", None)
                existing["brief_model_en"] = self.brief_model_en_var.get().strip()
                existing["brief_model_hi"] = self.brief_model_hi_var.get().strip()

            existing["secretary_model"] = self.secretary_model_var.get().strip()
            existing["ollama_host"]     = self.review_host_var.get().strip() or "http://localhost:11434"

            struct_model = self.struct_model_var.get().strip()
            if struct_model:
                existing["structure_model"] = struct_model
            else:
                existing.pop("structure_model", None)

            existing_by_id = {s["step_id"]: s for s in existing.get("review_steps", []) if "step_id" in s}
            merged_steps = []
            for sid, skip_v, refine_v in zip(self._step_ids, self.step_skippable_vars, self.step_refine_vars):
                step = dict(existing_by_id.get(sid, {"step_id": sid}))
                step["skippable"] = skip_v.get()
                step["refine"]    = refine_v.get()
                merged_steps.append(step)
            if merged_steps:
                existing["review_steps"] = merged_steps

            existing["telegram_enabled"]       = self.tg_enabled_var.get()
            existing["telegram_bot_token"]     = self.tg_token_var.get().strip()
            existing["telegram_chat_id"]       = self.tg_chat_var.get().strip()
            existing["morning_briefing_enabled"] = self.morning_enabled_var.get()
            try:
                existing["pending_task_lookback_days"] = int(self.pending_lookback_var.get())
            except ValueError:
                errors.append("Pending lookback days must be a whole number (e.g. 7, or 0 to disable)")
            try:
                existing["pending_task_warn_threshold"] = int(self.pending_warn_var.get())
            except ValueError:
                errors.append("Pending warn threshold must be a whole number (e.g. 3)")
            try:
                existing["pending_task_critical_threshold"] = int(self.pending_crit_var.get())
            except ValueError:
                errors.append("Pending critical threshold must be a whole number (e.g. 5)")
            existing["voice_control"]           = self.voice_ctrl_var.get()
            try:
                existing["voice_control_threshold"] = int(self.voice_threshold_var.get())
            except ValueError:
                errors.append("Voice control threshold must be a whole number (e.g. 500)")

            def _save_hhmm(raw, key, default, label):
                try:
                    datetime.datetime.strptime(raw, "%H:%M")
                    existing[key] = raw
                except ValueError:
                    errors.append(f"{label} must be in HH:MM format (e.g. {default})")
                    existing[key] = default

            _save_hhmm(self.morning_time_var.get().strip(),
                       "morning_briefing_time", "08:00", "Morning brief time")
            existing["evening_reminder_enabled"] = self.evening_reminder_var.get()
            _save_hhmm(self.evening_reminder_time_var.get().strip(),
                       "evening_reminder_time", "21:00", "Evening reminder time")

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
    try:
        import config_web_launcher
        config_web_launcher.launch_settings_app()
    except Exception:
        ctk.set_appearance_mode("dark")
        root = ctk.CTk()
        app  = ConfigApp(root)
        root.mainloop()
