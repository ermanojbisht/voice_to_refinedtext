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
SAMPLE_RATE = 16000
MODEL_SIZE = "small"
OLLAMA_MODEL = "qwen2.5:3b"

# ---- SILENCE DETECTION CONFIG ----
SILENCE_THRESHOLD = 300  # Adjust as needed (amplitude level)
SILENCE_DURATION = 2   # seconds of continuous silence to stop recording
CHUNK_SIZE = 1024        # Audio chunk size for processing

# ---- RECORD AUDIO ----
print("🎙 Recording...")
subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/service-login.oga"]) # Start beep

audio_buffer = []
silent_chunks = 0
recording = True

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE) as stream:
    while recording:
        chunk, overflowed = stream.read(CHUNK_SIZE)
        audio_buffer.append(chunk)

        if len(chunk) == 0:
            continue # Skip empty chunks

        # Calculate energy (RMS) of the chunk
        # Ensure chunk is float to avoid overflow with **2, then convert back if needed
        energy = np.sqrt(np.mean(chunk.astype(float)**2))

        if energy < SILENCE_THRESHOLD:
            silent_chunks += 1
            if (silent_chunks * CHUNK_SIZE / SAMPLE_RATE) >= SILENCE_DURATION:
                recording = False
        else:
            silent_chunks = 0

subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/service-logout.oga"]) # End beep

audio = np.concatenate(audio_buffer)
wav.write("input.wav", SAMPLE_RATE, audio)

# ---- TRANSCRIBE ----
print("🧠 Transcribing...")
model = WhisperModel(MODEL_SIZE, compute_type="int8")
segments, _ = model.transcribe("input.wav")

text = " ".join(seg.text for seg in segments)
print("📝 Raw text:", text)

# ---- SEND TO OLLAMA ----
prompt = f"""
You are an advanced text editor expert at cleaning and rewriting text obtained from speech transcription. Your task is to clean, format, and correct transcribed text from voice dictation.

INPUT TEXT:
{text}

INSTRUCTIONS:
1. Detect the dominant language (English or Hindi/Hinglish).
2. If the text is mostly English (>20%):
   - Correct grammar, spelling, and engineering terminology.
   - Output purely in English.
3. If the text is mostly Hindi/Hinglish (>80%):
   - Keep the flow natural but fix grammar.
   - Output ONLY in Devanagari script (Hindi).
   - DO NOT use Urdu script.
4. Remove filler words (uh, um, like, okay) and repetitions.
5. NEVER use Urdu / Arabic / Persian script.
6. Clean grammar, remove filler words, and rewrite clearly and professionally.
5. Do NOT add introductions ("Here is the corrected text") or explanations. Just output the final text.

OUTPUT:
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.1,
        "top_p": 0.9
    }
)

response_json = response.json()

if "error" in response_json:
    print(f"Error from Ollama: {response_json['error']}")
    final_text = "Error processing text with Ollama."
else:
    final_text = response_json["response"]
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

with open(log_file_path, 'w') as f:
    json.dump(log_data, f, indent=4)

print("📝 Logged to log.json")

# ---- COPY TO CLIPBOARD ----
subprocess.run(
    "xclip -selection clipboard",
    input=final_text.encode(),
    shell=True
)

print("✅ Copied to clipboard")
sys.exit(0)
