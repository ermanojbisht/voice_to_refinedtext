# Setup Summary

## What this project contains

This repository currently includes two distinct Python applications:

- **AI Voice Refiner / Evening Review**: the existing tray app and companion scripts. Dependencies are listed in `requirements.txt`; Ubuntu-specific convenience setup is in `install.sh`.
- **Audio to Ideas**: a separate GUI/CLI package in `audio_to_idea/`. Its packaging metadata is in `pyproject.toml`; see [its user guide](audio_to_idea/usage.md).

The dependency lists are separate and are not interchangeable.

## Current environment support

Ubuntu desktop is the target for the existing tray app. The README and setup guide record historical testing on Ubuntu 22.04 and 24.04. Ubuntu 26.04 has been brought up manually with a local venv, but that recovery has not yet been turned into a repeatable, release-tested setup. Other distributions, Windows, and macOS are not yet qualified.

Audio capture, clipboard access, tray icons, and global shortcuts depend on the OS and desktop session. The repository also does not yet have a complete CI matrix proving compatibility across Python versions.

## Ubuntu convenience install

Review `install.sh` before running it. It uses `apt`, may install Ollama, pulls models, creates a venv, links Ubuntu's system `gi` module, and configures an X11 hotkey. It is not a generic installer or a venv-only repair tool.

```bash
./install.sh
bash install_desktop.sh
```

The desktop launcher points to `.venv/bin/python`. Create a separate venv for each machine, operating system, and Python version; do not copy `.venv` between environments.

## Python dependency guidance

`requirements.txt` contains older exact pins and may not install on newer Python versions. Use only a Python/dependency combination verified for the selected app. `pyproject.toml` currently describes Audio to Ideas, not the tray app. Before claiming broader compatibility, consolidate and clarify dependency declarations and add CI checks for the declared Python versions.

On Ubuntu 26.04, the working tray-app setup uses Python 3.14 in a local venv with newer compatible dependencies and system-site packages for Ubuntu-provided modules. This documents one successful machine recovery; it is not yet a supported all-environments recipe.

## Basic checks

```bash
.venv/bin/python -c "import faster_whisper, numpy, scipy, sounddevice, pystray, pynput; print('imports OK')"
.venv/bin/python tray_app.py
```

Confirm microphone recording, transcription, local Ollama refinement, clipboard output, tray menu interaction, and the relevant hotkey in the target desktop session. For Wayland, follow the [Wayland Setup section in the README](../README.md#wayland-setup).
