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
import signal

# ---- TRAY ICON MANAGER ----

class VoiceAssistantTray:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.engine = VoiceEngine(self.script_dir)
        
        # Current app states
        self.is_recording = False
        self.is_processing = False
        self.running = True
        
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
        
        # Hotkey tracking
        self.pressed_keys = set()
        self.hotkey_combo = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('v')}
        self.hotkey_combo_alt = {keyboard.Key.ctrl_r, keyboard.Key.alt_r, keyboard.KeyCode.from_char('v')}
        
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

    def on_press(self, key):
        if key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.pressed_keys.add(keyboard.Key.ctrl_l if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl else keyboard.Key.ctrl_r)
        elif key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.pressed_keys.add(keyboard.Key.alt_l if key == keyboard.Key.alt_l or key == keyboard.Key.alt else keyboard.Key.alt_r)
        elif hasattr(key, 'char') and key.char == 'v':
            self.pressed_keys.add(keyboard.KeyCode.from_char('v'))
        
        # Check if combo is pressed
        if all(k in self.pressed_keys for k in [keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('v')]) or \
           all(k in self.pressed_keys for k in [keyboard.Key.ctrl_r, keyboard.Key.alt_r, keyboard.KeyCode.from_char('v')]):
            self.toggle_recording()

    def on_release(self, key):
        if key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.pressed_keys.discard(keyboard.Key.ctrl_l)
            self.pressed_keys.discard(keyboard.Key.ctrl_r)
        elif key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.pressed_keys.discard(keyboard.Key.alt_l)
            self.pressed_keys.discard(keyboard.Key.alt_r)
        elif hasattr(key, 'char') and key.char == 'v':
            self.pressed_keys.discard(keyboard.KeyCode.from_char('v'))

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
            # Start background task in a new thread so we don't block the listener
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

                # 3. Direct Typing if enabled
                if self.engine.config.get("DIRECT_TYPING"):
                    self.engine.type_text(final_text)
            
            # 4. Return to Idle State
            self.is_processing = False
            self.update_icon("idle")
            
        except Exception as e:
            print(f"Error in background process: {e}")
            self.is_recording = False
            self.is_processing = False
            self.update_icon("idle")

    def open_gui(self):
        """Launches the main GUI dashboard."""
        subprocess.Popen([sys.executable, os.path.join(self.script_dir, "main_gui.py")])

    def open_settings(self):
        """Launches the settings window."""
        subprocess.Popen([sys.executable, os.path.join(self.script_dir, "config_gui.py")])

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

    def exit_app(self, icon=None, item=None):
        """Signals the application components to stop."""
        print("Stopping application...")
        self.running = False
        if self.listener:
            self.listener.stop()
        if self.icon:
            self.icon.stop()

    def run(self):
        """Starts the tray icon and the hotkey listener."""
        # Setup signal handler for clean exit
        signal.signal(signal.SIGINT, lambda sig, frame: self.exit_app())
        signal.signal(signal.SIGTERM, lambda sig, frame: self.exit_app())

        try:
            self.listener.start() # Runs in background
            print("Tray application is running. Use the menu or Ctrl+Alt+V.")
            self.icon.run()       # This blocks until self.icon.stop() is called
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            self.exit_app()

if __name__ == "__main__":
    app = VoiceAssistantTray()
    app.run()
