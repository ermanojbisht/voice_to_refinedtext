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
            "en": "qwen2.5:3b",
            "hi": "mashriram/sarvam-1:latest"
        },
        "OLLAMA_HOST": "http://localhost:11434",
        "SILENCE_THRESHOLD": 300,
        "SILENCE_DURATION": 2,
        "TEMPERATURE": 0.1
    }
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            user_config = json.load(f)
            # Merge user config with defaults to ensure all keys exist
            default_config.update(user_config)
            return default_config
    return default_config

def get_model_for_lang(config, lang):
    """Returns the correct model for the detected language."""
    models = config.get("OLLAMA_MODELS", {})
    # Fallback order: Language specific -> Global OLLAMA_MODEL key -> Hardcoded default
    return models.get(lang, config.get("OLLAMA_MODEL", "qwen2.5:3b"))

def detect_lang(text):
    """Detects if text is Hindi or English."""
    try:
        lang = detect(text)
        return lang if lang in ["hi", "en"] else "en"
    except:
        return "en"

def get_prompt_and_stops(script_dir, model_name, text, lang):
    """Resolves the correct prompt template and stop tokens for a model."""
    prompts_dir = os.path.join(script_dir, "prompts")
    model_subdir = model_name.replace("/", "_").replace(":", "_")
    
    # Resolve model folder
    model_path = os.path.join(prompts_dir, model_name)
    if not os.path.exists(model_path):
        model_path = os.path.join(prompts_dir, model_subdir)
    if not os.path.exists(model_path):
        model_path = os.path.join(prompts_dir, "default")

    # Read prompt
    prompt_file = os.path.join(model_path, f"{lang}.txt")
    if os.path.exists(prompt_file):
        with open(prompt_file, "r") as f:
            prompt_template = f.read()
    else:
        prompt_template = "{text}"
    
    prompt = prompt_template.format(text=text)

    # Load stops
    stops_path = os.path.join(prompts_dir, "stops.json")
    stop_tokens = []
    if os.path.exists(stops_path):
        with open(stops_path, "r") as f:
            stops_data = json.load(f)
            # Try exact name, then underscore name, then default
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
    
    # 1. Strip <think>...</think> tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    # 2. Strip common meta-prefixes
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

    # 3. Strip surrounding quotes
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
        
    return text
