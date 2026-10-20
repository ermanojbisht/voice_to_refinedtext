#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import threading
import datetime
import json
import time
from typing import Optional, Dict, Any, List, Set, Tuple

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel
import utils
from pynput.keyboard import Controller
from audio_to_idea.resources import legacy_inference, legacy_recording

class VoiceEngine:
    """Central engine for recording, transcribing, and refining voice."""
    
    def __init__(self, script_dir):
        self.script_dir = script_dir
        self.config = utils.load_config(self.script_dir)
        self.stop_event = threading.Event()
        self._whisper_model = None  # Lazy load
        self._asr_provider = None   # Modular ASR provider
        self._stream_recorder = None # Pre-roll ring buffer & Silero VAD recorder
        self.keyboard = Controller()
        self.last_acoustic_suggestion = None
        self.last_acoustic_info = None

    def notify_acoustic_suggestion(self, suggestion: dict):
        """Displays non-blocking desktop notification advising about acoustic preset fit."""
        if not suggestion:
            return
        try:
            title = suggestion.get("title", "Language Advisory")
            msg = suggestion.get("message", "")
            is_warn = suggestion.get("severity") == "warning"
            urgency = "critical" if is_warn else "normal"
            icon = "dialog-warning" if is_warn else "dialog-information"
            subprocess.run(
                ["notify-send", "-u", urgency, "-i", icon, "-t", "8000", f"Voice Refiner: {title}", msg],
                timeout=3,
                check=False
            )
        except Exception:
            pass

    def reload_config(self):
        """Reloads config from disk and resets cached ASR provider."""
        self.config = utils.load_config(self.script_dir)
        if self._asr_provider is not None:
            try:
                self._asr_provider.close()
            except Exception:
                pass
            self._asr_provider = None
        if self._stream_recorder is not None:
            self._stream_recorder.silence_dur = float(self.config.get("SILENCE_DURATION", 2.5))
            self._stream_recorder.rms_threshold = int(self.config.get("SILENCE_THRESHOLD", 300))
            self._stream_recorder.pre_roll_ms = int(self.config.get("PRE_ROLL_BUFFER_MS", 500))
            self._stream_recorder.vad_threshold = float(self.config.get("VAD_THRESHOLD", 0.50))

    def get_active_preset(self) -> str:
        return self.config.get("ACTIVE_ASR_PRESET") or self.config.get("ACTIVE_MODEL_PROFILE", "smart_bilingual")

    def set_active_preset(self, preset_key: str):
        self.config["ACTIVE_ASR_PRESET"] = preset_key
        presets = self.config.get("ASR_PRESETS", {})
        if preset_key in presets:
            preset = presets[preset_key]
            self.config["ASR_ENGINE"] = preset.get("backend", "faster_whisper")
            self.config["ACTIVE_MODEL_PROFILE"] = preset_key
        if self._asr_provider is not None:
            try:
                self._asr_provider.close()
            except Exception:
                pass
            self._asr_provider = None

    def get_active_goal(self) -> str:
        return self.config.get("ACTIVE_REFINEMENT_GOAL") or self.config.get("LANGUAGE_MODE", "clean_bilingual")

    def set_active_goal(self, goal_key: str):
        self.config["ACTIVE_REFINEMENT_GOAL"] = goal_key
        goals = self.config.get("REFINEMENT_GOALS", {})
        if goal_key in goals:
            goal = goals[goal_key]
            self.config["LANGUAGE_MODE"] = goal.get("output_lang", "bilingual")
            self.config["MODE"] = "translate" if goal.get("translate") else "refine"

    def reprocess_last_audio(self, preset: Optional[str] = None, goal: Optional[str] = None) -> Dict[str, Any]:
        """Re-runs cached last recording (input.wav) through specified or active Preset and Goal without speaking."""
        wav_path = os.path.join(self.script_dir, "input.wav")
        if not os.path.isfile(wav_path):
            return {"ok": False, "error": "No cached audio recording found (input.wav is missing)."}

        old_preset = self.get_active_preset()
        old_goal = self.get_active_goal()

        if preset:
            self.set_active_preset(preset)
        if goal:
            self.set_active_goal(goal)

        try:
            raw_text = self.transcribe(wav_path)
            refined_text = self.refine(raw_text)
            return {
                "ok": True,
                "preset": self.get_active_preset(),
                "goal": self.get_active_goal(),
                "raw_text": raw_text,
                "final_text": refined_text,
                "text": refined_text,
                "acoustic_suggestion": self.last_acoustic_suggestion,
                "acoustic_info": self.last_acoustic_info,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            if preset and preset != old_preset:
                self.set_active_preset(old_preset)
            if goal and goal != old_goal:
                self.set_active_goal(old_goal)

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

    @property
    def stream_recorder(self):
        """Lazy loads the unified StreamRecorder with circular pre-roll and Silero VAD."""
        if self._stream_recorder is None:
            from audio_toolkit.recorder import StreamRecorder
            pre_roll_ms = self.config.get("PRE_ROLL_BUFFER_MS", 500)
            vad_thresh = self.config.get("VAD_THRESHOLD", 0.50)
            rms_thresh = self.config.get("SILENCE_THRESHOLD", 300)
            silence_dur = self.config.get("SILENCE_DURATION", 2.5)
            self._stream_recorder = StreamRecorder(
                sample_rate=self.config.get("SAMPLE_RATE", 16000),
                chunk_size=1024,
                pre_roll_ms=pre_roll_ms,
                silence_dur=silence_dur,
                vad_threshold=vad_thresh,
                rms_threshold=rms_thresh,
                script_dir=self.script_dir,
            )
        return self._stream_recorder

    @property
    def asr_provider(self):
        """Lazy loads the active modular ASR provider (Nemotron, Whisper, etc.)."""
        if self._asr_provider is None:
            from audio_to_idea.asr import ASRFactory
            self._asr_provider = ASRFactory.from_engine_config(self.config)
            self._asr_provider.load()
        return self._asr_provider

    @asr_provider.setter
    def asr_provider(self, value):
        self._asr_provider = value

    @property
    def filler_remover(self):
        """Lazy loads the microsecond in-memory filler word and stutter remover."""
        if getattr(self, "_filler_remover", None) is None:
            from pwd_helper.filler import FillerWordRemover
            custom = self.config.get("CUSTOM_FILLER_WORDS", [])
            collapse = self.config.get("COLLAPSE_STUTTERS", True)
            self._filler_remover = FillerWordRemover(custom_fillers=custom, collapse_stutters_enabled=collapse)
        return self._filler_remover

    @property
    def fuzzy_matcher(self):
        """Lazy loads the in-memory fuzzy n-gram custom word and domain dictionary engine."""
        if getattr(self, "_fuzzy_matcher", None) is None:
            from pwd_helper.fuzzy_matcher import FuzzyCustomWordMatcher, load_all_domain_words
            threshold = float(self.config.get("FUZZY_MATCH_THRESHOLD", 0.35))
            domain_words = load_all_domain_words(self.config)
            self._fuzzy_matcher = FuzzyCustomWordMatcher(domain_words, threshold=threshold)
        return self._fuzzy_matcher

    @legacy_recording
    def record(self, on_start=None, on_end=None, pre_record_notification=None, on_audio_chunk=None):
        """Records audio with pre-roll buffer, neural VAD, and manual stop support."""
        self.stop_event.clear()
        recorder = self.stream_recorder
        recorder.stop_event = self.stop_event

        # Sync runtime configuration
        recorder.silence_dur = float(self.config.get("SILENCE_DURATION", 2.5))
        recorder.rms_threshold = int(self.config.get("SILENCE_THRESHOLD", 300))
        recorder.pre_roll_ms = int(self.config.get("PRE_ROLL_BUFFER_MS", 500))
        recorder.vad_threshold = float(self.config.get("VAD_THRESHOLD", 0.50))
        play_sounds = self.config.get("FEATURES", {}).get("start_end_sounds", True)

        wav_path = os.path.join(self.script_dir, "input.wav")
        return recorder.record(
            output_wav=wav_path,
            on_start=on_start,
            on_end=on_end,
            pre_record_notification=pre_record_notification,
            play_sounds=play_sounds,
            on_audio_chunk=on_audio_chunk,
        )

    # Languages this app legitimately produces as final output.
    _ALLOWED_LANGS = {"en", "hi"}

    # Languages that are close enough to Hindi that Whisper confuses them with Hindi.
    # When detected, re-transcribe forcing "hi" to get proper Devanagari output.
    _HINDI_FAMILY  = {"hi", "ur", "pa", "mr", "gu", "ne", "sd", "bho"}

    # Balanced bilingual prompt allowing natural Hindi + English code-switching
    _BILINGUAL_PROMPT = "PWD civil works, road and bridge inspection, EE, AE, JE, NIT, MB, RCC, निविदा, सड़क निर्माण।"

    # Initial prompt that steers Whisper toward Devanagari script for Hindi audio while preserving technical terms.
    _HINDI_PROMPT  = "नमस्ते, यह हिंदी में है। PWD technical terms like EE, AE, JE, NIT, MB, RCC, Bridge inspection."

    @legacy_inference
    def transcribe(self, wav_path):
        """Converts audio file to raw text with language guard and hallucination filtering.

        Strategy:
        1. If ASR_ENGINE is configured, route to modular BaseASRProvider (Nemotron, etc.).
        2. Otherwise (or in legacy unit tests with mocked whisper_model), use WhisperModel
           with Hindi-family Devanagari steering and alpha filtering.
        """
        # 3-Portion Acoustic Language Identification & Non-Blocking Suggestion Check
        active_preset_key = self.get_active_preset()
        self.last_acoustic_suggestion = None
        self.last_acoustic_info = None

        if active_preset_key != "smart_bilingual" and isinstance(wav_path, str) and os.path.isfile(wav_path):
            try:
                from audio_to_idea.asr.acoustic_langid import AcousticLanguageDetector, get_acoustic_suggestion
                detector = AcousticLanguageDetector.get_instance()
                self.last_acoustic_info = detector.detect(wav_path)
                self.last_acoustic_suggestion = get_acoustic_suggestion(self.last_acoustic_info, active_preset_key)
                if self.last_acoustic_suggestion:
                    self.notify_acoustic_suggestion(self.last_acoustic_suggestion)
            except Exception:
                pass

        # 3. Audio Loading, Duration Check & Pause-Guided Chunker Guard
        pcm = None
        duration_s = 0.0
        if isinstance(wav_path, str) and os.path.isfile(wav_path):
            import scipy.signal as signal
            sr, data = wav.read(wav_path)
            if data.dtype == np.int16:
                pcm = data.astype(np.float32) / 32768.0
            else:
                pcm = data.astype(np.float32)
            if len(pcm.shape) > 1:
                pcm = pcm.mean(axis=1)
            if sr != 16000 and len(pcm) > 0:
                pcm = signal.resample(pcm, int(len(pcm) * 16000 / sr))
            duration_s = len(pcm) / 16000.0
        elif isinstance(wav_path, np.ndarray):
            pcm = wav_path.astype(np.float32)
            if len(pcm.shape) > 1:
                pcm = pcm.mean(axis=1)
            duration_s = len(pcm) / 16000.0

        pause_chunking_enabled = self.config.get("PAUSE_GUIDED_CHUNKING", True)
        chunk_max_s = float(self.config.get("CHUNK_MAX_SECONDS", 40.0))

        if pcm is not None and pause_chunking_enabled and duration_s > chunk_max_s:
            from audio_toolkit.chunker import PauseGuidedChunker
            chunker = PauseGuidedChunker(
                target_chunk_s=float(self.config.get("CHUNK_TARGET_SECONDS", 30.0)),
                min_chunk_s=float(self.config.get("CHUNK_MIN_SECONDS", 8.0)),
                max_chunk_s=chunk_max_s,
                min_pause_ms=int(self.config.get("CHUNK_MIN_PAUSE_MS", 250)),
            )
            chunks = chunker.chunk_audio(pcm)
            if len(chunks) > 1:
                parts = []
                for c in chunks:
                    t = self._transcribe_single(c.pcm)
                    if t and t.strip():
                        parts.append(t.strip())
                raw_text = " ".join(parts)
            else:
                raw_text = self._transcribe_single(pcm, wav_path=wav_path)
        else:
            raw_text = self._transcribe_single(pcm if pcm is not None else wav_path, wav_path=wav_path)

        # Microsecond In-Memory Filler Word & Stutter Removal (if enabled)
        features = self.config.get("FEATURES", {})
        if self.config.get("ENABLE_FILLER_REMOVAL", True) and features.get("filler_word_removal", True):
            try:
                raw_text = self.filler_remover.clean(raw_text, enabled=True)
            except Exception:
                pass

        # Fuzzy N-Gram Custom Domain Replacement Engine (if enabled)
        if self.config.get("ENABLE_FUZZY_CUSTOM_WORDS", True) and features.get("fuzzy_custom_words", True):
            try:
                raw_text = self.fuzzy_matcher.apply(raw_text)
            except Exception:
                pass

        # PWD Uttarakhand Terminology normalization (if enabled)
        if features.get("pwd_terminology_corrector", True):
            try:
                from pwd_helper.normalizer import normalize_pwd_terms
                raw_text = normalize_pwd_terms(raw_text)
            except Exception:
                pass

        return raw_text

    def _transcribe_single(self, audio_target, wav_path=None):
        """Transcribes a single chunk or short audio piece using the active ASR backend."""
        lang_mode = self.config.get("LANGUAGE_MODE", "bilingual")

        if not self.config.get("ASR_ENGINE") or self._whisper_model is not None:
            # Determine forced language and prompt based on language mode
            if lang_mode == "pure_english":
                forced_lang = "en"
                initial_prompt = "PWD civil works, road and bridge inspection, EE, AE, JE, NIT, MB, RCC."
            elif lang_mode == "pure_hindi":
                forced_lang = "hi"
                initial_prompt = self._HINDI_PROMPT
            else:
                forced_lang = None
                initial_prompt = self._BILINGUAL_PROMPT

            segments, info = self.whisper_model.transcribe(
                audio_target,
                language=forced_lang,
                initial_prompt=initial_prompt,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
            )

            if forced_lang is None and info.language in self._HINDI_FAMILY:
                # Re-transcribe with explicit Hindi + Devanagari prompt for clean output.
                segments, info = self.whisper_model.transcribe(
                    audio_target,
                    language="hi",
                    initial_prompt=self._HINDI_PROMPT,
                    condition_on_previous_text=False,
                    no_speech_threshold=0.6,
                    log_prob_threshold=-1.0,
                )
            elif forced_lang is None and info.language not in self._ALLOWED_LANGS:
                # Unrelated mis-detection → fall back to English.
                segments, info = self.whisper_model.transcribe(
                    audio_target,
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
        else:
            # Modular ASR provider path (Nemotron, Whisper-GGML, Handy-CLI)
            actual_wav_path = wav_path
            if isinstance(audio_target, np.ndarray):
                pcm = audio_target
            else:
                pcm = np.zeros(16000, dtype=np.float32)

            # Resolve ASR language and prompt from active preset if configured
            active_preset_key = self.get_active_preset()
            presets = self.config.get("ASR_PRESETS", {})
            active_preset = presets.get(active_preset_key, {})

            if active_preset and "asr_language" in active_preset:
                asr_lang = active_preset.get("asr_language")
                if asr_lang == "en":
                    prompt_text = "PWD civil works, road and bridge inspection, EE, AE, JE, NIT, MB, RCC."
                elif asr_lang == "hi":
                    prompt_text = self._HINDI_PROMPT
                else:
                    prompt_text = self._BILINGUAL_PROMPT
            else:
                if lang_mode == "pure_english":
                    asr_lang = "en"
                    prompt_text = "PWD civil works, road and bridge inspection, EE, AE, JE, NIT, MB, RCC."
                elif lang_mode == "pure_hindi":
                    asr_lang = "hi"
                    prompt_text = self._HINDI_PROMPT
                else:
                    asr_lang = None
                    prompt_text = self._BILINGUAL_PROMPT

            result = self.asr_provider.transcribe(
                pcm,
                wav_path=actual_wav_path,
                language=asr_lang,
                prompt=prompt_text,
            )
            return result.text

    def refine(self, text, mode=None, goal=None):
        """Sends text to Ollama for refinement/translation based on refinement goal."""
        if not text.strip():
            return "No speech detected."

        speech_class = utils.classify_speech_language(text)
        lang = "hi" if speech_class in ("pure_hindi", "mixed_devanagari_hinglish", "roman_hinglish") else "en"

        goals = self.config.get("REFINEMENT_GOALS", {})
        if goal:
            active_goal_key = goal
            active_goal = goals.get(active_goal_key, {})
            run_mode = active_goal.get("output_lang", "bilingual")
            is_translate = active_goal.get("translate", False)
            prompt_mode = goal
        elif mode:
            run_mode = mode
            mode_to_goal = {
                "bilingual": "clean_bilingual",
                "pure_english": "official_english",
                "pure_hindi": "official_hindi",
                "roman_hinglish": "roman_hinglish"
            }
            active_goal_key = mode_to_goal.get(mode, "clean_bilingual")
            active_goal = goals.get(active_goal_key, {})
            is_translate = (run_mode == "translate")
            prompt_mode = mode
        else:
            lang_mode = self.config.get("LANGUAGE_MODE")
            if lang_mode and lang_mode in {"pure_english", "pure_hindi", "roman_hinglish"}:
                run_mode = lang_mode
                prompt_mode = lang_mode
                mode_to_goal = {
                    "bilingual": "clean_bilingual",
                    "pure_english": "official_english",
                    "pure_hindi": "official_hindi",
                    "roman_hinglish": "roman_hinglish"
                }
                active_goal_key = mode_to_goal.get(lang_mode, lang_mode)
                active_goal = goals.get(active_goal_key, {})
                is_translate = (run_mode == "translate")
            else:
                active_goal_key = self.get_active_goal()
                active_goal = goals.get(active_goal_key, {})
                run_mode = active_goal.get("output_lang", "bilingual")
                is_translate = active_goal.get("translate", False)
                prompt_mode = active_goal_key or run_mode

        # Select model based on 4D goal attributes or run_mode
        active_goal = goals.get(active_goal_key, {})
        target_lang = active_goal.get("target_lang", run_mode)

        if is_translate:
            model_name = utils.get_translate_model(self.config, lang)
        elif target_lang == "pure_hindi" or run_mode in ("pure_hindi", "official_hindi") or active_goal_key == "official_hindi":
            model_name = self.config.get("OLLAMA_MODELS", {}).get("hi") or "SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest"
        elif target_lang == "pure_english" or run_mode in ("pure_english", "official_english") or active_goal_key == "official_english":
            model_name = self.config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")
        elif active_goal_key in ("ideas_actions", "concise_summary") or active_goal.get("intent") in ("ideas_actions", "concise_summary"):
            model_name = self.config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")
        elif run_mode == "bilingual" or active_goal_key == "clean_bilingual":
            # If input is pure English, route strictly to English model to prevent hallucinating Hindi/acronyms
            if speech_class == "pure_english":
                model_name = self.config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")
            else:
                model_name = self.config.get("OLLAMA_MODELS", {}).get("hi") or self.config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")
        else:
            model_name = utils.get_model_for_lang(self.config, lang)

        # Resolve prompt based on active goal or run_mode
        prompt, stops = utils.get_prompt_and_stops(self.script_dir, model_name, text, lang, mode=prompt_mode, config=self.config)

        keep_alive = self.config.get("OLLAMA_KEEP_ALIVE", "5m")
        temperature = self.config.get("TEMPERATURE", 0.0)
        response = utils.call_ollama(
            self.config.get("OLLAMA_HOST"), model_name, prompt, stops, 
            temperature,
            keep_alive=keep_alive
        )

        if "error" in response:
            result = f"Error: {response['error']}"
        else:
            result = utils.clean_response(response.get("response", ""))
            features = self.config.get("FEATURES", {})
            if features.get("pwd_terminology_corrector", True):
                try:
                    from pwd_helper.normalizer import normalize_pwd_terms
                    result = normalize_pwd_terms(result)
                except Exception:
                    pass

        # Build 4D role representation
        role_data = {
            "target_lang": active_goal.get("target_lang") or active_goal.get("output_lang", "bilingual"),
            "intent": active_goal.get("intent") or active_goal.get("format", "clean_paragraph"),
            "acronym_policy": active_goal.get("acronyms", "preserve_latin"),
            "action_mode": active_goal.get("action") or ("translate_and_refine" if is_translate else "refine_only")
        }

        # Log immediately with full 4D role and goal metadata
        self.log(
            text, result,
            lang=lang,
            mode=active_goal_key or run_mode,
            model=model_name,
            goal=active_goal_key or run_mode,
            role=role_data
        )
        return result

    def log(self, raw_text, final_text, lang="unknown", mode="unknown", model="unknown", asr=None, goal=None, role=None):
        """Logs the session to log.json with full metadata."""
        now = datetime.datetime.now()
        timestamp = now.isoformat()
        asr_profile = asr or self.config.get("ACTIVE_MODEL_PROFILE") or self.config.get("ASR_ENGINE", "whisper")
        goal_val = goal or mode
        if role is None:
            goals = self.config.get("REFINEMENT_GOALS", {})
            g_spec = goals.get(goal_val, {})
            role = {
                "target_lang": g_spec.get("target_lang") or g_spec.get("output_lang", "bilingual"),
                "intent": g_spec.get("intent") or g_spec.get("format", "clean_paragraph"),
                "acronym_policy": g_spec.get("acronyms", "preserve_latin"),
                "action_mode": g_spec.get("action", "refine_only"),
            }

        log_entry = {
            "timestamp": timestamp,
            "asr": asr_profile,
            "goal": goal_val,
            "role": role,
            "mode": goal_val,
            "lang": lang,
            "model": model,
            "raw_text": raw_text,
            "final_text": final_text,
            "acoustic_suggestion": self.last_acoustic_suggestion,
            "acoustic_info": self.last_acoustic_info
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
        """Saves a single note, transcript, and metadata to the central notes directory."""
        try:
            import storage_manager
            storage_manager.save_dictation_session(
                raw_text=entry.get('raw_text', ''),
                refined_text=entry.get('final_text', ''),
                preset=entry.get('asr', ''),
                goal=entry.get('mode', ''),
                model=entry.get('model', ''),
                save_markdown=True
            )
        except Exception as exc:
            raw_path = self.config.get("MARKDOWN_PATH", "~/Documents/VoiceNotes")
            folder = os.path.expanduser(raw_path)
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
        if self._stream_recorder is not None:
            self._stream_recorder.stop_recording()

    def paste_text(self, text: str) -> bool:
        """Pastes text at current cursor position using safe clipboard save & restore.

        Preserves user clipboard history, injects Ctrl+V key chord (or configured combo),
        waits quiet period, and restores original clipboard content.
        """
        if not text:
            return False
        time.sleep(0.1)
        try:
            from audio_toolkit import get_clipboard_manager
            mgr = get_clipboard_manager()
            paste_method = self.config.get("PASTE_METHOD", "clipboard_restore")
            delay_ms = int(self.config.get("PASTE_DELAY_MS", 150))
            key_combo = self.config.get("PASTE_KEY_COMBO", "ctrl_v")
            return mgr.paste_with_restore(text, paste_method=paste_method, delay_ms=delay_ms, key_combo=key_combo)
        except Exception as e:
            print(f"Error while pasting: {e}")
            return False

    def type_text(self, text):
        """Inserts text at the current cursor position.

        If PASTE_METHOD is 'direct_typing', simulates keyboard typing.
        Otherwise (default 'clipboard_restore' or 'clipboard_only'), routes to paste_text()
        for instant delivery and zero clipboard history loss.
        """
        if not text:
            return
        method = self.config.get("PASTE_METHOD", "clipboard_restore")
        if method != "direct_typing":
            return self.paste_text(text)

        # Legacy character-by-character typing:
        time.sleep(0.8)
        try:
            session = os.environ.get("XDG_SESSION_TYPE", "").lower()
            tool = self.config.get("TYPING_TOOL", "auto").lower()

            # Priority 1: ydotool on Wayland (highly reliable across compositors)
            if (tool == "ydotool" or (tool == "auto" and session == "wayland")) and subprocess.run(
                    ["which", "ydotool"], capture_output=True).returncode == 0:
                subprocess.run(["ydotool", "type", "--", text], check=False)
            # Priority 2: wtype on Wayland
            elif (tool == "wtype" or (tool == "auto" and session == "wayland")) and subprocess.run(
                    ["which", "wtype"], capture_output=True).returncode == 0:
                subprocess.run(["wtype", "--", text], check=False)
            # Priority 3: xdotool on X11 / XWayland
            elif (tool == "xdotool" or tool == "auto") and subprocess.run(
                    ["which", "xdotool"], capture_output=True).returncode == 0:
                subprocess.run(["xdotool", "type", "--clearmodifiers", "--", text], check=False)
            else:
                self.keyboard.type(text)
        except Exception as e:
            print(f"Error while typing: {e}")
