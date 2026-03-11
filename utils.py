import os
import json
import re
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
        "DIRECT_TYPING": False
    }
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                user_config = json.load(f)
                # Handle dictionary merge for nested configs
                for key in ["OLLAMA_MODELS", "OLLAMA_TRANSLATE_MODELS"]:
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

def get_prompt_and_stops(script_dir, model_name, text, lang, mode="refine"):
    """Resolves the correct prompt template and stop tokens for a model and mode."""
    prompts_dir = os.path.join(script_dir, "prompts")
    model_subdir = model_name.replace("/", "_").replace(":", "_")
    
    model_path = os.path.join(prompts_dir, model_name)
    if not os.path.exists(model_path):
        model_path = os.path.join(prompts_dir, model_subdir)
    if not os.path.exists(model_path):
        model_path = os.path.join(prompts_dir, "default")

    prefix = f"{mode}_" if mode != "refine" else ""
    prompt_file = os.path.join(model_path, f"{prefix}{lang}.txt")
    
    if os.path.exists(prompt_file):
        with open(prompt_file, "r") as f:
            prompt_template = f.read()
    else:
        fallback_file = os.path.join(model_path, f"{lang}.txt")
        if os.path.exists(fallback_file):
            with open(fallback_file, "r") as f:
                prompt_template = f.read()
        else:
            prompt_template = "{text}"
    
    prompt = prompt_template.format(text=text)

    stops_path = os.path.join(prompts_dir, "stops.json")
    stop_tokens = []
    if os.path.exists(stops_path):
        with open(stops_path, "r") as f:
            stops_data = json.load(f)
            stop_tokens = stops_data.get(model_name, stops_data.get(model_subdir, stops_data["default"]))[lang]
    
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
