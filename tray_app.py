#!/usr/bin/env python3
import os
import pystray
from PIL import Image, ImageDraw
from pynput import keyboard
import threading
import subprocess
import time
import json
from engine import VoiceEngine
import sys

# ---- TRAY ICON MANAGER ----

class VoiceAssistantTray:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.engine = VoiceEngine(self.script_dir)
        
        # Current app states
        self.is_recording = False
        self.is_processing = False
        
        # Generate initial icons
        self.icons = {
            "idle": self.create_status_icon("#45475a"),   # Gray/Slate
            "recording": self.create_status_icon("#f38ba8"), # Red
            "processing": self.create_status_icon("#89b4fa") # Blue
        }
        
        # Setup the tray icon
        self.icon = pystray.Icon(
            "AI Voice Refiner",
            self.icons["idle"],
            menu=pystray.Menu(
                pystray.MenuItem("Start Recording", self.toggle_recording),
                pystray.MenuItem(lambda item: f"Mode: {self.engine.config.get('MODE', 'refine').capitalize()}", self.cycle_mode),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Open Dashboard", self.open_gui),
                pystray.MenuItem("Settings", self.open_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.exit_app)
            )
        )
        
        # Global Hotkey Listener (Ctrl + Alt + V)
        self.hotkey = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+v': self.toggle_recording
        })

    def create_status_icon(self, color):
        """Generates a simple 64x64 circle icon for the tray."""
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Draw a circle with the specified color
        draw.ellipse((8, 8, 56, 56), fill=color)
        return image

    def update_icon(self, state):
        """Switches the tray icon image based on current activity."""
        self.icon.icon = self.icons.get(state, self.icons["idle"])

    def toggle_recording(self):
        """The main action triggered by the hotkey or menu."""
        if not self.is_recording and not self.is_processing:
            # Start background task in a new thread so we don't block the hotkey listener
            threading.Thread(target=self.run_full_process, daemon=True).start()
        elif self.is_recording:
            # Signal the engine to stop recording immediately
            self.engine.stop_recording()

    def run_full_process(self):
        """Orchestrates the full Record -> Transcribe -> Refine cycle."""
        try:
            # 1. Start Recording State
            self.is_recording = True
            self.update_icon("recording")
            
            # This blocks until recording finishes (either by silence or manual stop)
            wav_path = self.engine.record()
            
            # 2. Start Processing State
            self.is_recording = False
            self.is_processing = True
            self.update_icon("processing")
            
            # Transcription & Refinement
            raw_text = self.engine.transcribe(wav_path)
            if raw_text.strip():
                final_text = self.engine.refine(raw_text)
                
                # Copy to clipboard
                subprocess.run("xclip -selection clipboard", input=final_text.encode(), shell=True)
                
                # Success sound & logging
                self.engine.log(raw_text, final_text)
                subprocess.run(["paplay", os.path.join(self.script_dir, "sounds", "complete.oga")])
            
            # 3. Return to Idle State
            self.is_processing = False
            self.update_icon("idle")
            
        except Exception as e:
            print(f"Error in background process: {e}")
            self.is_recording = False
            self.is_processing = False
            self.update_icon("idle")

    def open_gui(self):
        """Launches the main GUI dashboard."""
        subprocess.Popen(["python3", os.path.join(self.script_dir, "main_gui.py")])

    def open_settings(self):
        """Launches the settings window."""
        subprocess.Popen(["python3", os.path.join(self.script_dir, "config_gui.py")])

    def cycle_mode(self, icon, item):
        """Toggles between Refine and Translate modes."""
        current = self.engine.config.get("MODE", "refine")
        new_mode = "translate" if current == "refine" else "refine"
        
        # Update config in memory and on disk
        self.engine.config["MODE"] = new_mode
        with open(os.path.join(self.script_dir, "config.json"), "w") as f:
            json.dump(self.engine.config, f, indent=4)
        
        # Force redraw menu label
        self.icon.update_menu()

    def exit_app(self):
        """Cleans up and exits the application."""
        self.hotkey.stop()
        self.icon.stop()
        sys.exit(0)

    def run(self):
        """Starts the tray icon and the hotkey listener."""
        self.hotkey.start() # Runs in background
        self.icon.run()     # This blocks until app is closed

if __name__ == "__main__":
    app = VoiceAssistantTray()
    app.run()
