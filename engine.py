#!/usr/bin/env python3
import os
import subprocess
import threading
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel
import utils
import datetime
import json
import time
from pynput.keyboard import Controller

class VoiceEngine:
    """Central engine for recording, transcribing, and refining voice."""
    
    def __init__(self, script_dir):
        self.script_dir = script_dir
        self.config = utils.load_config(self.script_dir)
        self.stop_event = threading.Event()
        self._whisper_model = None  # Lazy load
        self.keyboard = Controller()

    @property
    def whisper_model(self):
        """Lazy loads the Whisper model to save memory when not in use."""
        if self._whisper_model is None:
            model_size = self.config.get("WHISPER_MODEL", "large-v3-turbo")
            try:
                import torch
                if torch.cuda.is_available():
                    self._whisper_model = WhisperModel(model_size, device="cuda", compute_type="float16")
                else:
                    self._whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            except Exception:
                self._whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        return self._whisper_model

    def record(self, on_start=None, on_end=None, pre_record_notification=None):
        """Records audio with silence detection and manual stop support."""
        samplerate = self.config.get("SAMPLE_RATE", 16000)
        threshold = self.config.get("SILENCE_THRESHOLD", 300)
        silence_dur = self.config.get("SILENCE_DURATION", 2.0)
        chunk_size = 1024

        audio_buffer = []
        silent_chunks = 0
        self.stop_event.clear()

        if pre_record_notification:
            try:
                subprocess.run(
                    ["notify-send", "-i", "dialog-information", "Evening Review", pre_record_notification],
                    timeout=5,
                    check=False
                )
            except Exception:
                pass

        if on_start: on_start()

        play_sounds = self.config.get("FEATURES", {}).get("start_end_sounds", True)
        if play_sounds:
            subprocess.run(["paplay", os.path.join(self.script_dir, "sounds", "start.oga")], check=False)

        with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', blocksize=chunk_size) as stream:
            while not self.stop_event.is_set():
                chunk, _ = stream.read(chunk_size)
                audio_buffer.append(chunk)

                energy = np.sqrt(np.mean(chunk.astype(float)**2))
                if energy < threshold:
                    silent_chunks += 1
                    if (silent_chunks * chunk_size / samplerate) >= silence_dur:
                        break
                else:
                    silent_chunks = 0

        if play_sounds:
            subprocess.run(["paplay", os.path.join(self.script_dir, "sounds", "end.oga")], check=False)
        if on_end: on_end()

        audio = np.concatenate(audio_buffer)
        wav_path = os.path.join(self.script_dir, "input.wav")
        wav.write(wav_path, samplerate, audio)
        return wav_path

    # Languages this app legitimately produces as final output.
    _ALLOWED_LANGS = {"en", "hi"}

    # Languages that are close enough to Hindi that Whisper confuses them with Hindi.
    # When detected, re-transcribe forcing "hi" to get proper Devanagari output.
    _HINDI_FAMILY  = {"hi", "ur", "pa", "mr", "gu", "ne", "sd", "bho"}

    # Initial prompt that steers Whisper toward Devanagari script for Hindi audio.
    _HINDI_PROMPT  = "नमस्ते, यह हिंदी में है।"

    def transcribe(self, wav_path):
        """Converts audio file to raw text with language guard and hallucination filtering.

        Strategy:
        1. Auto-detect language first (no constraint).
        2. If detected language is Hindi-family (hi/ur/pa/mr/gu…) → re-transcribe
           forcing "hi" with a Devanagari initial_prompt so script is correct.
        3. If detected language is English → keep result as-is.
        4. Anything else (unrelated language mis-detection) → force "en".
        """
        segments, info = self.whisper_model.transcribe(
            wav_path,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
        )

        if info.language in self._HINDI_FAMILY:
            # Re-transcribe with explicit Hindi + Devanagari prompt for clean output.
            segments, info = self.whisper_model.transcribe(
                wav_path,
                language="hi",
                initial_prompt=self._HINDI_PROMPT,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
            )
        elif info.language not in self._ALLOWED_LANGS:
            # Unrelated mis-detection → fall back to English.
            segments, info = self.whisper_model.transcribe(
                wav_path,
                language="en",
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
            )

        parts = []
        for seg in segments:
            if seg.no_speech_prob > 0.6:
                continue
            text = seg.text.strip()
            if not text:
                continue
            # Pure-numeral/punctuation segments are hallucinations (no alphabetic chars)
            if sum(1 for c in text if c.isalpha()) == 0:
                continue
            parts.append(text)
        return " ".join(parts)

    def refine(self, text, mode=None):
        """Sends text to Ollama for refinement/translation based on language."""
        if not text.strip():
            return "No speech detected."

        lang = utils.detect_lang(text)

        # Use provided mode or fall back to config
        run_mode = mode or self.config.get("MODE", "refine")

        # Select model based on mode
        if run_mode == "translate":
            model_name = utils.get_translate_model(self.config, lang)
        else:
            model_name = utils.get_model_for_lang(self.config, lang)

        # Resolve prompt based on mode (e.g., translate_hi.txt)
        prompt, stops = utils.get_prompt_and_stops(self.script_dir, model_name, text, lang, mode=run_mode)

        response = utils.call_ollama(
            self.config.get("OLLAMA_HOST"), model_name, prompt, stops, 
            self.config.get("TEMPERATURE", 0.1)
        )

        if "error" in response:
            result = f"Error: {response['error']}"
        else:
            result = utils.clean_response(response.get("response", ""))

        # Log immediately with more metadata
        self.log(text, result, lang=lang, mode=run_mode, model=model_name)
        return result

    def log(self, raw_text, final_text, lang="unknown", mode="unknown", model="unknown"):
        """Logs the session to log.json with full metadata."""
        now = datetime.datetime.now()
        timestamp = now.isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "mode": mode,
            "lang": lang,
            "model": model,
            "raw_text": raw_text,
            "final_text": final_text
        }
        
        # 1. Save to JSON log
        log_file = os.path.join(self.script_dir, "log.json")
        data = []
        if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
            with open(log_file, 'r') as f:
                try: data = json.load(f)
                except: data = []
        data.append(log_entry)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # 2. Save to Markdown if enabled
        if self.config.get("SAVE_TO_MARKDOWN"):
            self.save_markdown(log_entry, now)

    def save_markdown(self, entry, now):
        """Saves a single note to a Markdown file."""
        raw_path = self.config.get("MARKDOWN_PATH", "~/Documents/VoiceNotes")
        folder = os.path.expanduser(raw_path)
        
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            
        filename = now.strftime("%Y-%m-%d_%H%M%S.md")
        filepath = os.path.join(folder, filename)
        
        content = f"""# Voice Note - {now.strftime("%Y-%m-%d %H:%M:%S")}
**Mode**: {entry['mode']}
**Language**: {entry['lang']}
**Model**: {entry['model']}

## Refined Text
{entry['final_text']}

---
## Raw Transcription
{entry['raw_text']}
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def refine_with_prompt(self, full_prompt, structure_model=None):
        """Call Ollama with a fully pre-built prompt string (used for per-step structuring).

        structure_model: explicit model name from review_config["structure_model"].
        Falls back to the English refiner model from the main config.
        """
        model_name = structure_model or utils.get_model_for_lang(self.config, "en")
        response = utils.call_ollama(
            self.config.get("OLLAMA_HOST"), model_name, full_prompt, [],
            self.config.get("TEMPERATURE", 0.1)
        )
        if "error" in response:
            return f"Error: {response['error']}"
        return utils.clean_response(response.get("response", ""))

    def get_raw_transcription(self, wav_path):
        return self.transcribe(wav_path)

    def stop_recording(self):
        """Force stops the recording process."""
        self.stop_event.set()

    def type_text(self, text):
        """Simulates keyboard typing to insert text at the current cursor position."""
        if not text:
            return
        try:
            # Small delay to ensure the user has switched focus if needed
            time.sleep(0.5)
            self.keyboard.type(text)
        except Exception as e:
            print(f"Error while typing: {e}")
