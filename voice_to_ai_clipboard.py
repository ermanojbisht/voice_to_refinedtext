#!/usr/bin/env python3
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import subprocess
import requests
from faster_whisper import WhisperModel

import sys
import subprocess # Added for playing sounds
import os # Added for file existence checks
import datetime # Added for timestamp generation
import json # Added for JSON logging

# ---- CONFIG ----
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

default_config = {
    "SAMPLE_RATE": 16000,
    "WHISPER_MODEL": "large-v3-turbo",
    "OLLAMA_MODEL": "qwen2.5:3b",
    "SILENCE_THRESHOLD": 300,
    "SILENCE_DURATION": 2,
    "TEMPERATURE": 0.1
}

if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
else:
    config = default_config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

SAMPLE_RATE = config.get("SAMPLE_RATE", 16000)
MODEL_SIZE = config.get("WHISPER_MODEL", "large-v3-turbo")
OLLAMA_MODEL = config.get("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_HOST = config.get("OLLAMA_HOST", "http://localhost:11434")
SILENCE_THRESHOLD = config.get("SILENCE_THRESHOLD", 300)
SILENCE_DURATION = config.get("SILENCE_DURATION", 2)
TEMPERATURE = config.get("TEMPERATURE", 0.1)

# ---- SOUND PATHS ----
START_SOUND = os.path.join(script_dir, "sounds", "start.oga")
END_SOUND = os.path.join(script_dir, "sounds", "end.oga")
COMPLETE_SOUND = os.path.join(script_dir, "sounds", "complete.oga")

# ---- SILENCE DETECTION CONFIG ----
CHUNK_SIZE = 1024        # Audio chunk size for processing

# ---- RECORD AUDIO ----
print(f"🎙 Recording (Model: {MODEL_SIZE}, Ollama: {OLLAMA_MODEL}, Host: {OLLAMA_HOST})...")
# Sound 1: Start Recording
subprocess.run(["paplay", START_SOUND])

audio_buffer = []
silent_chunks = 0
recording = True

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE) as stream:
    while recording:
        chunk, _ = stream.read(CHUNK_SIZE)
        audio_buffer.append(chunk)

        # Calculate energy (RMS) of the chunk
        energy = np.sqrt(np.mean(chunk.astype(float)**2))

        if energy < SILENCE_THRESHOLD:
            silent_chunks += 1
            if (silent_chunks * CHUNK_SIZE / SAMPLE_RATE) >= SILENCE_DURATION:
                recording = False
        else:
            silent_chunks = 0

# Sound 2: End Recording
subprocess.run(["paplay", END_SOUND])

audio = np.concatenate(audio_buffer)
wav_path = os.path.join(script_dir, "input.wav")
wav.write(wav_path, SAMPLE_RATE, audio)

from langdetect import detect, DetectorFactory
# Ensure consistent results
DetectorFactory.seed = 0

def detect_lang(text):
    try:
        return detect(text)
    except:
        return "en"

# ---- TRANSCRIBE ----
print("🧠 Transcribing...")
model = WhisperModel(MODEL_SIZE, compute_type="int8")
segments, _ = model.transcribe(wav_path)

text = " ".join(seg.text for seg in segments)
print("📝 Raw text:", text)

# ---- LANGUAGE DETECTION & PROMPT SELECTION ----
lang = detect_lang(text)
if lang not in ["hi", "en"]:
    lang = "en"  # Default to English if detection is ambiguous
print(f"🌍 Detected Language: {lang}")

# Resolve prompt and stops from directory structure
prompts_dir = os.path.join(script_dir, "prompts")
model_subdir = OLLAMA_MODEL.replace("/", "_").replace(":", "_") # Fallback to underscore-based names
# Try exact match, then try the underscore version
model_path = os.path.join(prompts_dir, OLLAMA_MODEL)
if not os.path.exists(model_path):
    model_path = os.path.join(prompts_dir, model_subdir)

# Default to "default" if model folder doesn't exist
if not os.path.exists(model_path):
    model_path = os.path.join(prompts_dir, "default")

prompt_file = os.path.join(model_path, f"{lang}.txt")

# Read the prompt
if os.path.exists(prompt_file):
    with open(prompt_file, "r") as f:
        prompt_template = f.read()
else:
    # Fallback to absolute default
    prompt_template = "{text}"

prompt = prompt_template.format(text=text)

# Load stops
stops_path = os.path.join(prompts_dir, "stops.json")
with open(stops_path, "r") as f:
    stops_data = json.load(f)

# Get stops for model or default
stop_tokens = stops_data.get(OLLAMA_MODEL, stops_data.get(model_subdir, stops_data["default"]))[lang]

response = requests.post(
    f"{OLLAMA_HOST}/api/generate",
    json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "temperature": TEMPERATURE,
        "top_p": 0.9,
        "stop": stop_tokens
    }
)

response_json = response.json()

if "error" in response_json:
    print(f"Error from Ollama: {response_json['error']}")
    final_text = "Error processing text with Ollama."
else:
    final_text = response_json["response"].strip()
    # Model-specific post-processing to clean up meta-chatter
    prefixes_to_strip = [
        "Professional English:", "Cleaned text:", "Refined text:",
        "यहाँ सुधार हुआ पाठ है:", "शुद्ध रूप:", "संवाद:", "Raw:", "Output:",
        "The professional version of the text is:", "Here is the refined text:","Correct and cleaned transcription:","Correct and cleaned text:","Correct and cleaned:","यहाँ सुधार के लिए पाठ है:","Correct and cleaned:"
    ]
    for prefix in prefixes_to_strip:
        if final_text.lower().startswith(prefix.lower()):
            final_text = final_text[len(prefix):].strip()

    # Remove any surrounding quotes if the model added them
    if final_text.startswith('"') and final_text.endswith('"'):
        final_text = final_text[1:-1].strip()

print("✨ Final text:", final_text)

# ---- LOGGING ----
import datetime
log_entry = {
    "timestamp": datetime.datetime.now().isoformat(),
    "raw_text": text,
    "final_text": final_text
}

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.json")
log_data = []

if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
    with open(log_file_path, 'r') as f:
        try:
            log_data = json.load(f)
        except json.JSONDecodeError:
            # Handle case where file is not valid JSON, start fresh
            log_data = []

log_data.append(log_entry)

with open(log_file_path, 'w', encoding='utf-8') as f:
    json.dump(log_data, f, indent=4, ensure_ascii=False)

print("📝 Logged to log.json")

# ---- COPY TO CLIPBOARD ----
subprocess.run(
    "xclip -selection clipboard",
    input=final_text.encode(),
    shell=True
)

print("✅ Copied to clipboard")
# Sound 3: Processing Complete
subprocess.run(["paplay", COMPLETE_SOUND])
sys.exit(0)
