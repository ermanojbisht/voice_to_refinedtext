#!/usr/bin/env python3
import os
import subprocess
import sys
from engine import VoiceEngine

# ---- SETUP ----
script_dir = os.path.dirname(os.path.abspath(__file__))
engine = VoiceEngine(script_dir)

def main():
    print(f"🎙 Listening (Whisper: {engine.config.get('WHISPER_MODEL')})...")
    
    # 1. Record
    wav_path = engine.record()
    
    # 2. Transcribe
    print("🧠 Transcribing...")
    raw_text = engine.transcribe(wav_path)
    print(f"📝 Raw: {raw_text}")
    
    if not raw_text.strip():
        print("❌ No speech detected.")
        sys.exit(0)

    # 3. Refine
    print("✨ Refining...")
    final_text = engine.refine(raw_text)
    print(f"✅ Final: {final_text}")

    # 4. Clipboard & Success sound
    subprocess.run("xclip -selection clipboard", input=final_text.encode(), shell=True)
    subprocess.run(["paplay", os.path.join(script_dir, "sounds", "complete.oga")])
    
    print("📋 Copied to clipboard.")

if __name__ == "__main__":
    main()
