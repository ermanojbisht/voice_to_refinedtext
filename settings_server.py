#!/usr/bin/env python3
"""Lightweight local web settings daemon for AI Voice Refiner.

Serves the glassmorphic settings web application and REST API on 127.0.0.1.
Zero external dependencies (uses standard library http.server).
"""
import os
import sys
import json
import queue
import socket
import threading
import urllib.request
import urllib.error
from copy import deepcopy
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import utils
from manual_service import manual_service
import mimetypes
import urllib.parse
import subprocess
import base64
from audio_to_idea.web_service import AudioIdeaWebService, urllib_quote
from audio_to_idea.templates import MODES
from refiner_service import RefinerService
import pwd_service
from review_service import ReviewService

DEFAULT_PORT = 8765


def get_configured_port() -> int:
    """Returns the settings daemon port from env var, config.json, or default (8765)."""
    env_port = os.environ.get("VOICE_REFINER_SETTINGS_PORT")
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass
    cfg = load_main_config()
    try:
        return int(cfg.get("SETTINGS_PORT", DEFAULT_PORT))
    except (ValueError, TypeError):
        return DEFAULT_PORT

_FEATURE_DEFS = [
    ("start_end_sounds", "🔔 Start / End Sounds", "Play audio cues when recording starts and stops."),
    ("clipboard_output", "📋 Clipboard Output", "Copy refined text to clipboard automatically after processing."),
    ("markdown_output", "📝 Markdown Output", "Also save refined text to the Markdown notes file."),
    ("direct_typing", "⌨ Direct Typing", "Type refined text directly at the cursor position (xdotool / ydotool)."),
    ("evening_review", "🌙 Evening Review", "Show 'Start Evening Review' in tray menu. Disable to use Voice Refiner only."),
    ("pwd_terminology_corrector", "🏛 PWD Terminology Corrector", "Auto-capitalizes and normalizes PWD abbreviations (NIT, MB, EE, RCC, SOR) in transcripts."),
    ("filler_word_removal", "✂️ Microsecond Filler Word Remover", "ON (Gain): Strips verbal hesitations ('um', 'uh', 'you know', 'मतलब') in <0.1ms, speeds up LLM generation, collapses stutters ('I I I' → 'I'), and restores sentence capitalization. OFF (Tradeoff): Preserves 100% verbatim raw speech for legal/interview forensic accuracy."),
    ("fuzzy_custom_words", "🔤 Fuzzy N-Gram Domain Dictionary", "ON (Gain): Repairs split speech acronyms ('Chat G P T' → 'ChatGPT', 'Charge B' → 'ChargeBee', 'D P R' → 'DPR', 'R and D' → 'R&D') and phonetic near-misses in <1ms without calling an LLM. Preserves boundary punctuation and ALL-CAPS/Titlecase. OFF (Tradeoff): Leaves raw split tokens character-for-character as emitted by Whisper/Nemotron without any domain word substitution."),
    ("terminal_rich_hud", "💻 Live Terminal Dictation HUD", "ON (Gain): Displays animated audio VU meter, VAD speech status, and color-coded panels during 'pwd_cli.py --listen' in the terminal. Automatically isolates clean output when piping. OFF (Tradeoff): Output is minimal unstyled plain text."),
]


def load_main_config() -> Dict[str, Any]:
    cfg_path = os.path.join(SCRIPT_DIR, "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_review_config() -> Dict[str, Any]:
    rev_path = os.path.join(SCRIPT_DIR, "review_config.json")
    try:
        with open(rev_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_ollama_models(host: str = "http://localhost:11434") -> List[str]:
    url = f"{host.rstrip('/')}/api/tags"
    req = urllib.request.Request(url, headers={"User-Agent": "VoiceAssistantSettings/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return [
            "qwen2.5:3b",
            "qwen2.5:7b",
            "llama3-hindi",
            "SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest",
            "aya-expanse:8b"
        ]


def handle_api_request(path: str, method: str, body: bytes | None = None) -> tuple[int, str]:
    """Pure API dispatcher for TTS and modular services (suitable for testing and routing)."""
    method = method.upper()
    if method == "GET":
        if path == "/api/tts/status":
            try:
                import pwd_helper.tts as tts
                return 200, json.dumps(tts.get_status())
            except Exception as e:
                return 500, json.dumps({"error": str(e)})

        if path == "/api/tts/voices":
            voices = [
                {"id": "ni_delhi_corp_f", "name": "Delhi Corporate Female", "gender": "female", "lang": "en-IN"},
                {"id": "ni_kahani_f", "name": "Warm Kahani / Storyteller Female", "gender": "female", "lang": "en-IN / hi"},
                {"id": "ni_air_anchor_m", "name": "AIR / Doordarshan Anchor Male", "gender": "male", "lang": "en-IN / hi"},
                {"id": "ni_ncr_tech_m", "name": "Noida / NCR Tech Explainer Male", "gender": "male", "lang": "en-IN"},
                {"id": "ni_fm_rj_f", "name": "Delhi FM Radio Host Female", "gender": "female", "lang": "en-IN"},
                {"id": "ni_docu_deep_m", "name": "Deep North Indian Documentary Male", "gender": "male", "lang": "en-IN"},
                {"id": "hf_alpha", "name": "Stock North Indian Broadcast Female", "gender": "female", "lang": "hi"},
                {"id": "hf_beta", "name": "Stock Warm Conversational Female", "gender": "female", "lang": "hi"},
                {"id": "hm_omega", "name": "Stock Authoritative Baritone Male", "gender": "male", "lang": "hi"},
                {"id": "hm_psi", "name": "Stock Modern Syllabic Male", "gender": "male", "lang": "hi"},
            ]
            return 200, json.dumps({"ok": True, "voices": voices})

    elif method == "POST":
        payload = {}
        if body:
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception:
                pass

        if path == "/api/tts/speak":
            text = payload.get("text", "")
            blocking = payload.get("blocking", False)
            speed = float(payload.get("speed", 1.0))
            lang = payload.get("lang", "auto")
            voice = payload.get("voice")
            cfg = payload.get("config") or {}
            if voice:
                cfg["voice"] = voice
                cfg["kokoro_voice"] = voice
                cfg["kokoro_voice_en"] = voice
                cfg["kokoro_voice_hi"] = voice
            try:
                import pwd_helper.tts as tts
                ok = tts.speak(text, lang=lang, blocking=blocking, speed=speed, config=cfg)
                return 200, json.dumps({"ok": ok})
            except Exception as e:
                return 500, json.dumps({"ok": False, "error": str(e)})

        if path == "/api/tts/stop":
            try:
                import pwd_helper.tts as tts
                tts.stop()
                return 200, json.dumps({"ok": True, "message": "Speech stopped"})
            except Exception as e:
                return 500, json.dumps({"ok": False, "error": str(e)})

    return 404, json.dumps({"error": f"Endpoint '{path}' not found"})


class SettingsHandler(BaseHTTPRequestHandler):
    server_version = "VoiceAssistantSettings/2.0"

    def log_message(self, format, *args):
        # Keep stdout clean; suppress routine GET/POST logs
        pass

    def _send_json(self, data: Any, status: int = 200):
        try:
            body = json.dumps(data, default=str, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _stream_audio(self, raw_path: str):
        filepath = urllib.parse.unquote(raw_path)
        path = os.path.abspath(os.path.expanduser(filepath))
        if not os.path.isfile(path):
            self.send_error(404, "Audio file not found")
            return

        file_size = os.path.getsize(path)
        mime_type = mimetypes.guess_type(path)[0] or "audio/mpeg"
        range_header = self.headers.get("Range")

        if range_header and range_header.startswith("bytes="):
            try:
                parts = range_header[6:].split("-")
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if parts[1] else file_size - 1
                if start >= file_size or end >= file_size or start > end:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{file_size}")
                    self.end_headers()
                    return

                length = end - start + 1
                self.send_response(206)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                with open(path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(remaining, 65536))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
                return
            except Exception:
                return

        # Full content response
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def do_GET(self):
        url_parts = self.path.split("?", 1)
        path = url_parts[0]
        query = urllib.parse.parse_qs(url_parts[1]) if len(url_parts) > 1 else {}

        if path.startswith("/api/tts/"):
            status_code, body_str = handle_api_request(path, "GET", None)
            self._send_json(json.loads(body_str), status=status_code)
            return

        svc = AudioIdeaWebService.get_instance()

        if path == "/" or path == "/index.html":
            html_file = os.path.join(SCRIPT_DIR, "web_settings", "index.html")
            if os.path.isfile(html_file):
                with open(html_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "web_settings/index.html not found")
            return

        if path in {"/audio-to-idea", "/audio-to-idea/", "/audio-to-idea/index.html"}:
            html_file = os.path.join(SCRIPT_DIR, "web_audio_to_idea", "index.html")
            if os.path.isfile(html_file):
                with open(html_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "web_audio_to_idea/index.html not found")
            return

        if path in {"/dashboard", "/dashboard/", "/dashboard/index.html"}:
            html_file = os.path.join(SCRIPT_DIR, "web_dashboard", "index.html")
            if os.path.isfile(html_file):
                with open(html_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "web_dashboard/index.html not found")
            return

        if path in {"/pwd-lookup", "/pwd-lookup/", "/pwd-lookup/index.html"}:
            html_file = os.path.join(SCRIPT_DIR, "web_pwd", "index.html")
            if os.path.isfile(html_file):
                with open(html_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "web_pwd/index.html not found")
            return

        if path in {"/review", "/review/", "/review/index.html"}:
            html_file = os.path.join(SCRIPT_DIR, "web_review", "index.html")
            if os.path.isfile(html_file):
                with open(html_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "web_review/index.html not found")
            return

        if path in {"/manual", "/manual/", "/manual.html", "/docs", "/docs/"}:
            try:
                from manual_service import manual_service
                html_file = manual_service.generate_html_manual()
            except Exception:
                html_file = os.path.join(SCRIPT_DIR, "docs", "generated", "manual.html")
            if os.path.isfile(html_file):
                with open(html_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "docs/generated/manual.html not found")
            return

        if path == "/api/health":
            self._send_json({"status": "ok", "pid": os.getpid()})
            return

        if path == "/api/doctor":
            try:
                import doctor
                rep = doctor.run_all_checks(run_mic=False)
                self._send_json(rep.to_dict())
            except Exception as exc:
                self._send_json({"error": str(exc), "overall_status": "FAIL"}, 500)
            return

        if path == "/api/refiner/status":
            ref_svc = RefinerService.get_instance()
            self._send_json(ref_svc.get_status())
            return

        if path == "/api/pwd/terms":
            self._send_json(pwd_service.get_all_terms())
            return

        if path == "/api/review/state":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.get_state())
            return

        if path == "/api/review/note_preview":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.get_note_preview())
            return

        if path == "/api/config":
            main_cfg = load_main_config()
            review_cfg = load_review_config()
            # Never send the bot token back to the browser; it is stored in .env.
            review_cfg["telegram_bot_token"] = ""
            profiles = list(main_cfg.get("MODEL_PROFILES", {}).keys())
            if not profiles:
                profiles = ["nemotron_fast", "whisper_large_v3", "whisper_turbo", "hinglish_apex"]

            self._send_json({
                "main": main_cfg,
                "review": review_cfg,
                "profiles": profiles,
                "model_profiles": main_cfg.get("MODEL_PROFILES", {}),
                "active_profile": main_cfg.get("ACTIVE_MODEL_PROFILE", profiles[0]),
                "asr_presets": main_cfg.get("ASR_PRESETS", {}),
                "active_preset": main_cfg.get("ACTIVE_ASR_PRESET", "smart_bilingual"),
                "refinement_goals": main_cfg.get("REFINEMENT_GOALS", {}),
                "active_goal": main_cfg.get("ACTIVE_REFINEMENT_GOAL", "clean_bilingual"),
                "whisper_fallback_model": main_cfg.get("WHISPER_FALLBACK_MODEL", "large-v3-turbo"),
                "global_hotkey": utils.get_global_hotkey(main_cfg),
                "features_def": [{"key": k, "label": lbl, "note": note} for k, lbl, note in _FEATURE_DEFS]
            })
            return

        if path == "/api/models":
            host = load_main_config().get("OLLAMA_HOST", "http://localhost:11434")
            models = get_ollama_models(host)
            self._send_json({"models": models})
            return

        # --- Audio to Ideas Endpoints ---
        if path == "/api/audio_to_idea/state":
            with svc.items_lock:
                items_copy = deepcopy(svc.items)
            ref_svc = RefinerService.get_instance()
            main_cfg = load_main_config()
            active_goal = ref_svc.engine.get_active_goal()
            current_mode = active_goal if active_goal in MODES else svc.settings.data["synthesis"].get("mode", "clean_bilingual")
            active_preset = ref_svc.engine.get_active_preset()
            asr_presets = main_cfg.get("ASR_PRESETS", {})
            goals_dict = main_cfg.get("REFINEMENT_GOALS", {})
            self._send_json({
                "items": items_copy,
                "selected_id": svc.selected_id,
                "busy": svc.is_busy(),
                "watching": svc.is_watching(),
                "watcher_folder": svc.watcher_folder,
                "modes": MODES,
                "goals": goals_dict,
                "current_mode": current_mode,
                "active_asr_preset": active_preset,
                "asr_presets": asr_presets,
                "profiles": svc.get_profiles(),
                "current_profile": svc.settings.data["synthesis"]["context_profile"] or "",
                "settings": svc.settings.data,
            })
            return

        if path == "/api/audio_to_idea/item_detail":
            item_id = query.get("id", [None])[0]
            if not item_id:
                self._send_json({"error": "Missing 'id' parameter"}, status=400)
                return
            detail = svc.get_item_detail(item_id)
            if detail:
                self._send_json(detail)
            else:
                self._send_json({"error": f"Item '{item_id}' not found"}, status=404)
            return

        if path == "/api/audio_to_idea/prompt":
            mode = query.get("mode", [svc.settings.data["synthesis"]["mode"]])[0]
            try:
                info = svc.get_prompt_info(mode)
                self._send_json(info)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=400)
            return

        if path == "/api/audio_to_idea/doctor":
            try:
                report = svc.run_doctor()
                self._send_json(report)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        if path == "/api/audio_to_idea/audio_stream":
            raw_path = query.get("path", [None])[0]
            if not raw_path:
                self.send_error(400, "Missing path parameter")
                return
            self._stream_audio(raw_path)
            return

        if path == "/api/audio_to_idea/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            q = svc.subscribe_events()
            try:
                # Send initial ping
                self.wfile.write(b": connected\n\n")
                self.wfile.flush()
                while True:
                    try:
                        evt = q.get(timeout=10.0)
                        msg = f"data: {json.dumps(evt, ensure_ascii=False)}\n\n".encode("utf-8")
                        self.wfile.write(msg)
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, IOError):
                pass
            finally:
                svc.unsubscribe_events(q)
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        path = self.path.split("?")[0]
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b"{}"

        if path.startswith("/api/tts/"):
            status_code, body_str = handle_api_request(path, "POST", body_bytes)
            self._send_json(json.loads(body_str), status=status_code)
            return

        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception as e:
            self._send_json({"ok": False, "error": f"Invalid JSON payload: {e}"}, status=400)
            return

        svc = AudioIdeaWebService.get_instance()

        if path == "/api/open_manual":
            try:
                mode = payload.get("mode", "browser") if isinstance(payload, dict) else "browser"
                theme = payload.get("theme", None) if isinstance(payload, dict) else None
                if mode == "app":
                    import manual_launcher
                    manual_launcher.launch_manual_app(theme=theme)
                    self._send_json({"ok": True, "message": "Manual launched in app window"})
                else:
                    manual_service.open_in_browser()
                    self._send_json({"ok": True, "message": "Manual opened in browser"})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        if path == "/api/test_telegram":
            try:
                import telegram_service
                ok, msg = telegram_service.test_connection(payload)
                self._send_json({"ok": ok, "message": msg})
            except Exception as e:
                self._send_json({"ok": False, "message": f"Connection error: {e}"})
            return

        if path == "/api/save":
            errors = []
            main_patch = payload.get("main", {})
            review_patch = payload.get("review", {})

            if main_patch:
                try:
                    cfg_file = os.path.join(SCRIPT_DIR, "config.json")
                    existing_main = load_main_config()
                    existing_main.update(main_patch)
                    with open(cfg_file, "w", encoding="utf-8") as f:
                        json.dump(existing_main, f, indent=4, ensure_ascii=False)

                    models_to_ensure = set([
                        existing_main.get("OLLAMA_MODELS", {}).get("en", ""),
                        existing_main.get("OLLAMA_MODELS", {}).get("hi", ""),
                        existing_main.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_en", ""),
                        existing_main.get("OLLAMA_TRANSLATE_MODELS", {}).get("to_hi", ""),
                    ])
                    for m in models_to_ensure:
                        if m:
                            utils.ensure_model_prompts(SCRIPT_DIR, m, existing_main)

                    if "GLOBAL_HOTKEY" in main_patch:
                        try:
                            utils.sync_system_hotkey(existing_main.get("GLOBAL_HOTKEY", "Ctrl+Space"))
                        except Exception:
                            pass
                    
                    try:
                        import engine
                        engine.reload_config()
                        ref_svc = RefinerService.get_instance()
                        ref_svc.engine.reload_config()
                    except Exception:
                        pass
                except Exception as e:
                    errors.append(f"config.json save error: {e}")

            if review_patch:
                try:
                    rev_file = os.path.join(SCRIPT_DIR, "review_config.json")
                    existing_rev = load_review_config()
                    from pwd_helper.secrets import set_secret
                    entered_token = str(review_patch.get("telegram_bot_token", "")).strip()
                    legacy_token = str(existing_rev.get("telegram_bot_token", "")).strip()
                    if entered_token:
                        set_secret("TELEGRAM_BOT_TOKEN", entered_token)
                    elif legacy_token:
                        # Migrate a token from older config files on the next save.
                        set_secret("TELEGRAM_BOT_TOKEN", legacy_token)
                    review_patch["telegram_bot_token"] = ""
                    existing_rev.update(review_patch)
                    with open(rev_file, "w", encoding="utf-8") as f:
                        json.dump(existing_rev, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    errors.append(f"review_config.json save error: {e}")

            if errors:
                self._send_json({"ok": False, "errors": errors}, status=500)
            else:
                self._send_json({"ok": True, "message": "Settings saved successfully!"})
            return

        if path == "/api/clean_cache":
            try:
                import storage_manager
                days = int(payload.get("retention_days", 7))
                res = storage_manager.clean_garbage(retention_days=days)
                self._send_json(res)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # --- Audio to Ideas POST Endpoints ---
        if path == "/api/audio_to_idea/add":
            paths = payload.get("paths", [])
            root = payload.get("input_root")
            added = svc.add_paths(paths, root)
            self._send_json({"ok": True, "added_count": len(added), "total_count": len(svc.items)})
            return

        if path == "/api/audio_to_idea/remove":
            item_id = payload.get("id", "")
            ok = svc.remove_item(item_id)
            self._send_json({"ok": ok})
            return

        if path == "/api/audio_to_idea/clear":
            completed_only = payload.get("completed_only", False)
            svc.clear_queue(completed_only)
            self._send_json({"ok": True, "remaining_count": len(svc.items)})
            return

        if path == "/api/audio_to_idea/select":
            item_id = payload.get("id")
            svc.selected_id = item_id
            self._send_json({"ok": True, "selected_id": item_id})
            return

        if path == "/api/audio_to_idea/save_edit":
            item_id = payload.get("id")
            text = payload.get("text", "")
            try:
                res = svc.save_transcript(item_id, text)
                self._send_json(res)
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=400)
            return

        if path == "/api/audio_to_idea/run":
            res = svc.start_processing(
                summary=payload.get("summary", True),
                selected_only=payload.get("selected_only", False),
                mode=payload.get("mode"),
                profile=payload.get("profile"),
                context=payload.get("context", ""),
                preset=payload.get("preset"),
            )
            status_code = 200 if res.get("ok") else 400
            self._send_json(res, status=status_code)
            return

        if path == "/api/audio_to_idea/stop":
            self._send_json(svc.stop_processing())
            return

        if path == "/api/audio_to_idea/set_mode":
            mode = payload.get("mode", "")
            if mode and mode in MODES:
                svc.settings.data["synthesis"]["mode"] = mode
                ref_svc = RefinerService.get_instance()
                ref_svc.set_goal(mode)
                self._send_json({"ok": True, "mode": mode, "status": ref_svc.get_status()})
            else:
                self._send_json({"ok": False, "error": f"Invalid mode: {mode}"}, status=400)
            return

        if path == "/api/audio_to_idea/watch":
            action = payload.get("action", "start")
            if action == "start":
                res = svc.start_watcher(
                    folder=payload.get("folder", ""),
                    context=payload.get("context", ""),
                    profile=payload.get("profile"),
                )
                self._send_json(res, status=200 if res.get("ok") else 400)
            else:
                self._send_json(svc.stop_watcher())
            return

        if path == "/api/audio_to_idea/prompt/preview":
            try:
                preview = svc.preview_prompt(
                    mode=payload.get("mode"),
                    text=payload.get("text", ""),
                    item_id=payload.get("item_id"),
                    context=payload.get("context", ""),
                    profile_path=payload.get("profile"),
                )
                self._send_json({"ok": True, "preview": preview})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=400)
            return

        if path == "/api/audio_to_idea/prompt/save":
            try:
                res = svc.save_prompt(
                    mode=payload.get("mode"),
                    text=payload.get("text", ""),
                    custom_folder=payload.get("custom_folder"),
                )
                self._send_json(res)
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=400)
            return

        if path == "/api/audio_to_idea/settings":
            patch = payload.get("patch", {})
            try:
                res = svc.update_audio_settings(patch)
                self._send_json(res)
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=400)
            return

        if path == "/api/audio_to_idea/browse":
            kind = payload.get("kind", "files")
            paths = svc.browse_dialog(kind)
            self._send_json({"ok": True, "paths": paths})
            return

        if path == "/api/audio_to_idea/open_folder":
            folder_path = payload.get("path")
            if folder_path and os.path.exists(folder_path):
                subprocess.Popen(["xdg-open", folder_path])
                self._send_json({"ok": True})
            else:
                self._send_json({"ok": False, "error": "Folder does not exist"}, status=404)
            return

        # --- Voice Refiner Dashboard Endpoints ---
        if path == "/api/refiner/record":
            ref_svc = RefinerService.get_instance()
            self._send_json(ref_svc.start_recording())
            return

        if path == "/api/refiner/stop":
            ref_svc = RefinerService.get_instance()
            self._send_json(ref_svc.stop_recording())
            return

        if path == "/api/refiner/cycle_preset":
            ref_svc = RefinerService.get_instance()
            new_preset = ref_svc.cycle_preset()
            self._send_json({"ok": True, "active_preset": new_preset, "status": ref_svc.get_status()})
            return

        if path == "/api/refiner/set_preset":
            ref_svc = RefinerService.get_instance()
            p = payload.get("preset", "")
            if p:
                ref_svc.set_preset(p)
                self._send_json({"ok": True, "active_preset": p, "status": ref_svc.get_status()})
            else:
                self._send_json({"ok": False, "error": "Missing preset"}, status=400)
            return

        if path == "/api/refiner/cycle_goal":
            ref_svc = RefinerService.get_instance()
            new_goal = ref_svc.cycle_goal()
            self._send_json({"ok": True, "active_goal": new_goal, "status": ref_svc.get_status()})
            return

        if path == "/api/refiner/set_goal":
            ref_svc = RefinerService.get_instance()
            g = payload.get("goal", "")
            if g:
                ref_svc.set_goal(g)
                self._send_json({"ok": True, "active_goal": g, "status": ref_svc.get_status()})
            else:
                self._send_json({"ok": False, "error": "Missing goal"}, status=400)
            return

        if path in {"/api/refiner/reprocess_last", "/api/reprocess_last"}:
            ref_svc = RefinerService.get_instance()
            preset = payload.get("preset")
            goal = payload.get("goal")
            res = ref_svc.reprocess_last(preset=preset, goal=goal)
            status_code = 200 if res.get("ok") else 400
            self._send_json(res, status=status_code)
            return

        if path == "/api/refiner/cycle_mode":
            ref_svc = RefinerService.get_instance()
            new_mode = ref_svc.cycle_language_mode()
            self._send_json({"ok": True, "language_mode": new_mode})
            return

        if path == "/api/refiner/cycle_profile":
            ref_svc = RefinerService.get_instance()
            new_prof = ref_svc.cycle_asr_profile()
            self._send_json({"ok": True, "active_profile": new_prof})
            return

        # --- PWD Glossary Endpoints ---
        if path == "/api/pwd/search":
            q = payload.get("query", "")
            terms = pwd_service.search_terms(q)
            self._send_json({"ok": True, "query": q, "terms": terms})
            return

        if path == "/api/pwd/add_custom":
            abbr = payload.get("abbr", "")
            english = payload.get("english", "")
            hindi = payload.get("hindi", "")
            cat = payload.get("category", "custom")
            res = pwd_service.add_custom_term(abbr, english, hindi, cat)
            status_code = 200 if res.get("ok") else 400
            self._send_json(res, status=status_code)
            return

        if path == "/api/pwd/translate":
            text = payload.get("text", "")
            mode = payload.get("mode", "auto")
            res = pwd_service.translate_sandbox(text, mode=mode)
            self._send_json({"ok": True, "result": res})
            return

        # --- Executive Evening Review Endpoints ---
        if path == "/api/review/start":
            rev_svc = ReviewService.get_instance()
            date_str = payload.get("date")
            self._send_json(rev_svc.start_review(date_str))
            return

        if path == "/api/review/record":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.start_recording())
            return

        if path == "/api/review/stop":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.stop_recording())
            return

        if path == "/api/review/upload_clip":
            rev_svc = ReviewService.get_instance()
            b64_data = payload.get("data", "")
            filename = payload.get("filename", "clip.wav")
            try:
                # Remove header if data URL format (e.g. data:audio/wav;base64,...)
                if "," in b64_data:
                    b64_data = b64_data.split(",", 1)[1]
                raw_bytes = base64.b64decode(b64_data)
                res = rev_svc.upload_clip(raw_bytes, filename)
                self._send_json(res, status=200 if res.get("ok") else 400)
            except Exception as exc:
                self._send_json({"ok": False, "error": f"Base64 decode failed: {exc}"}, status=400)
            return

        if path == "/api/review/update_clip":
            rev_svc = ReviewService.get_instance()
            idx = int(payload.get("index", 0))
            new_text = payload.get("text", "")
            res = rev_svc.update_clip(idx, new_text)
            self._send_json(res, status=200 if res.get("ok") else 400)
            return

        if path == "/api/review/delete_clip":
            rev_svc = ReviewService.get_instance()
            idx = int(payload.get("index", 0))
            res = rev_svc.delete_clip(idx)
            self._send_json(res, status=200 if res.get("ok") else 400)
            return

        if path == "/api/review/advance":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.advance_step())
            return

        if path == "/api/review/skip":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.skip_step())
            return

        if path == "/api/review/redo":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.redo_step())
            return

        if path == "/api/review/cancel":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.cancel_review())
            return

        if path == "/api/review/resolve_task":
            rev_svc = ReviewService.get_instance()
            task = payload.get("task", "")
            note_date = payload.get("note_date", "")
            self._send_json(rev_svc.resolve_task(task, note_date))
            return

        if path == "/api/review/replay_narration":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.replay_narration())
            return

        if path == "/api/review/stop_narration":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.stop_narration())
            return

        if path == "/api/review/regen_brief":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.regen_brief())
            return

        if path == "/api/review/open_in_obsidian":
            rev_svc = ReviewService.get_instance()
            self._send_json(rev_svc.open_in_obsidian())
            return

        self.send_error(404, "Endpoint not found")


class ReusableHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def run_server(port: int = None):
    if port is None:
        port = get_configured_port()
    server = ReusableHTTPServer(("127.0.0.1", port), SettingsHandler)
    print(f"[settings_server] Listening on http://127.0.0.1:{port}")
    server.serve_forever()


def start_server_daemon(port: int = None) -> int:
    """Starts server in background thread if not already running."""
    if port is None:
        port = get_configured_port()
    if is_port_in_use(port):
        # Verify health
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1.0) as resp:
                data = json.loads(resp.read().decode())
                if data.get("status") == "ok":
                    return port
        except Exception:
            pass

    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()
    return port


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else get_configured_port()
    try:
        run_server(port)
    except KeyboardInterrupt:
        print("\n[settings_server] Stopped.")
