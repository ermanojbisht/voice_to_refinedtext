import os
import json
import re
import logging
import requests
from langdetect import detect, DetectorFactory

# Ensure consistent language detection
DetectorFactory.seed = 0

def load_config(script_dir):
    """Loads config.json or returns defaults."""
    config_path = os.path.join(script_dir, "config.json")
    default_config = {
        "SAMPLE_RATE": 16000,
        "WHISPER_MODEL": "large-v3-turbo",
        "OLLAMA_MODELS": {
            "en": "qwen3.5:0.8b",
            "hi": "mashriram/sarvam-1:latest"
        },
        "OLLAMA_TRANSLATE_MODELS": {
            "to_en": "qwen2.5:3b",
            "to_hi": "mashriram/sarvam-1:latest"
        },
        "OLLAMA_HOST": "http://localhost:11434",
        "SILENCE_THRESHOLD": 300,
        "SILENCE_DURATION": 2,
        "TEMPERATURE": 0.1,
        "MODE": "refine",  # Options: "refine", "translate"
        "SAVE_TO_MARKDOWN": False,
        "MARKDOWN_PATH": "~/Documents/VoiceNotes",
        "DIRECT_TYPING": False,
        "FEATURES": {
            "start_end_sounds": True,
            "clipboard_output": True,
            "markdown_output": False,
            "direct_typing": False,
            "evening_review": True,
        }
    }
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                user_config = json.load(f)
                # Handle dictionary merge for nested configs
                for key in ["OLLAMA_MODELS", "OLLAMA_TRANSLATE_MODELS", "FEATURES"]:
                    if key in user_config and isinstance(user_config[key], dict):
                        default_config[key].update(user_config[key])
                        user_config.pop(key)
                
                # Merge remaining user config
                default_config.update(user_config)
                return default_config
            except:
                return default_config
    return default_config

def get_model_for_lang(config, lang):
    """Returns the correct model for the detected language in 'refine' mode."""
    models = config.get("OLLAMA_MODELS", {})
    return models.get(lang, config.get("OLLAMA_MODEL", "qwen2.5:3b"))

def get_translate_model(config, source_lang):
    """Returns the correct model for translation based on the target language."""
    target_key = "to_en" if source_lang == "hi" else "to_hi"
    trans_models = config.get("OLLAMA_TRANSLATE_MODELS", {})
    return trans_models.get(target_key, get_model_for_lang(config, source_lang))

def detect_lang(text):
    """Detects if text is Hindi, Urdu, or English."""
    try:
        lang = detect(text)
        if lang in ["hi", "ur"]:
            return "hi"
        return "en" if lang == "en" else "en"
    except:
        return "en"

def resolve_model_alias(model_name, config=None):
    """Return the short alias used as the prompts/ folder name for a model.

    Lookup order:
    1. model_aliases in config: if model_name is a value, return the matching key.
    2. model_aliases in config: if model_name is already a key, return it as-is.
    3. Auto-generate: take the last path component, strip the :tag suffix,
       replace non-alphanumeric chars with _, lowercase, trim to 40 chars.

    This is the single source of truth for folder resolution so callers never
    need to manually sanitise model names.
    """
    if config:
        aliases = config.get("model_aliases", {})
        for alias, full_name in aliases.items():
            if full_name == model_name:
                return alias
        if model_name in aliases:
            return model_name
    # Auto-generate a short folder name from the model string
    name = model_name.split("/")[-1]          # last path segment
    name = name.split(":")[0]                  # drop :tag
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return name[:40]


def ensure_model_prompts(script_dir, model_name, config=None):
    """Create a prompts/<alias>/ folder for a model if one does not yet exist.

    Copies the four template files from prompts/default/ as a starting point,
    then adds a default stop-token entry to stops.json.  Safe to call every
    time settings are saved — it is a no-op when the folder already exists.

    Returns the alias string that was used as the folder name.
    """
    import shutil
    alias = resolve_model_alias(model_name, config)
    prompts_dir = os.path.join(script_dir, "prompts")
    model_dir   = os.path.join(prompts_dir, alias)

    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
        default_dir = os.path.join(prompts_dir, "default")
        for fname in ("en.txt", "hi.txt", "translate_en.txt", "translate_hi.txt"):
            src = os.path.join(default_dir, fname)
            dst = os.path.join(model_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, dst)
            else:
                with open(dst, "w", encoding="utf-8") as fh:
                    fh.write("{text}\n")

    # Ensure stops.json has an entry for this alias
    stops_path = os.path.join(prompts_dir, "stops.json")
    try:
        with open(stops_path, "r", encoding="utf-8") as fh:
            stops = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        stops = {}
    if alias not in stops:
        default_stops = stops.get("default", {"hi": ["\n\n"], "en": ["\n\n"]})
        stops[alias] = {"hi": list(default_stops.get("hi", ["\n\n"])),
                        "en": list(default_stops.get("en", ["\n\n"]))}
        with open(stops_path, "w", encoding="utf-8") as fh:
            json.dump(stops, fh, ensure_ascii=False, indent=4)

    return alias


def get_prompt_and_stops(script_dir, model_name, text, lang, mode="refine", config=None):
    """Resolve the correct prompt template and stop tokens for a model and mode.

    Resolution order for the prompts/ folder:
    1. resolve_model_alias(model_name, config) → prompts/<alias>/
    2. prompts/<model_name_sanitised>/   (legacy fallback)
    3. prompts/default/
    """
    prompts_dir  = os.path.join(script_dir, "prompts")
    alias        = resolve_model_alias(model_name, config)
    model_subdir = model_name.replace("/", "_").replace(":", "_")

    for candidate in (alias, model_subdir, "default"):
        path = os.path.join(prompts_dir, candidate)
        if os.path.exists(path):
            model_path = path
            break
    else:
        model_path = os.path.join(prompts_dir, "default")

    prefix       = f"{mode}_" if mode != "refine" else ""
    prompt_file  = os.path.join(model_path, f"{prefix}{lang}.txt")
    fallback_file = os.path.join(model_path, f"{lang}.txt")

    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as fh:
            prompt_template = fh.read()
    elif os.path.exists(fallback_file):
        with open(fallback_file, "r", encoding="utf-8") as fh:
            prompt_template = fh.read()
    else:
        prompt_template = "{text}"

    prompt = prompt_template.format(text=text)

    stops_path  = os.path.join(prompts_dir, "stops.json")
    stop_tokens = []
    if os.path.exists(stops_path):
        with open(stops_path, "r", encoding="utf-8") as fh:
            stops_data = json.load(fh)
        stop_tokens = (
            stops_data.get(model_name)
            or stops_data.get(alias)
            or stops_data.get(model_subdir)
            or stops_data.get("default", {})
        ).get(lang, [])

    return prompt, stop_tokens

def call_ollama(host, model, prompt, stop_tokens, temperature=0.1, timeout=120):
    """Sends a request to Ollama and handles timeouts/errors."""
    try:
        response = requests.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "top_p": 0.9,
                "stop": stop_tokens
            },
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}

def get_logger(name, log_file=None):
    """Return a named logger. Adds a FileHandler the first time log_file is provided.

    Call pattern:
        # at module level (no file yet):
        _logger = utils.get_logger("tray")
        # at startup when log path is known:
        utils.get_logger("tray", log_file="/path/to/review_debug.log")
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Logger already configured — add file handler if newly provided
        if log_file and not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            ))
            logger.addHandler(fh)
        return logger

    fmt = logging.Formatter(
        "[%(asctime)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


def clean_response(text):
    """Strips <think> tags, prefixes, and surrounding quotes."""
    if not text:
        return ""

    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    prefixes_to_strip = [
        "Professional English:", "Cleaned text:", "Refined text:",
        "यहाँ सुधार हुआ पाठ है:", "शुद्ध रूप:", "संवाद:", "Raw:", "Output:",
        "The professional version of the text is:", "Here is the refined text:",
        "Correct and cleaned transcription:", "Correct and cleaned text:",
        "Correct and cleaned:", "यहाँ सुधार के लिए पाठ है:"
    ]

    for prefix in prefixes_to_strip:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()

    return text
