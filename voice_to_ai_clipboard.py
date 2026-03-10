#!/usr/bin/env python3
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import subprocess
import sys
import os
import json
import datetime
from faster_whisper import WhisperModel

# Import common utilities
import utils

# ---- CONFIG ----
script_dir = os.path.dirname(os.path.abspath(__file__))
config = utils.load_config(script_dir)

SAMPLE_RATE = config.get("SAMPLE_RATE", 16000)
MODEL_SIZE = config.get("WHISPER_MODEL", "large-v3-turbo")
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
print(f"🎙 Recording (Whisper: {MODEL_SIZE}, Host: {OLLAMA_HOST})...")
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

# ---- TRANSCRIBE ----
print("🧠 Transcribing...")
model = WhisperModel(MODEL_SIZE, compute_type="int8")
segments, _ = model.transcribe(wav_path)

text = " ".join(seg.text for seg in segments)
print("📝 Raw text:", text)

# ---- REFINEMENT ----
lang = utils.detect_lang(text)
OLLAMA_MODEL = utils.get_model_for_lang(config, lang)
print(f"🌍 Detected Language: {lang}, Using Model: {OLLAMA_MODEL}")

prompt, stop_tokens = utils.get_prompt_and_stops(script_dir, OLLAMA_MODEL, text, lang)
response_json = utils.call_ollama(OLLAMA_HOST, OLLAMA_MODEL, prompt, stop_tokens, TEMPERATURE)

if "error" in response_json:
    print(f"❌ Error from Ollama: {response_json['error']}")
    final_text = f"Error processing text with Ollama ({response_json['error']})."
else:
    final_text = utils.clean_response(response_json.get("response", ""))

print("✨ Final text:", final_text)

# ---- LOGGING ----
log_entry = {
    "timestamp": datetime.datetime.now().isoformat(),
    "raw_text": text,
    "final_text": final_text
}

log_file_path = os.path.join(script_dir, "log.json")
log_data = []

if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
    with open(log_file_path, 'r') as f:
        try:
            log_data = json.load(f)
        except json.JSONDecodeError:
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
