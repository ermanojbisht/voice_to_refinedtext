#!/usr/bin/env bash
# ==============================================================================
# Voice Refiner — Terminal Voice Typing Helper (Bash / Zsh)
# ==============================================================================
# Usage:
#   source scripts/terminal_voice.sh
#
# Provides:
#   v          - Speaks and dictates with live Rich Terminal HUD
#   voice-cmd  - Speaks a shell command and places it directly onto your prompt
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python"

if [ ! -x "${PYTHON_BIN}" ]; then
    PYTHON_BIN="python3"
fi

# Quick voice dictation alias
alias v="${PYTHON_BIN} ${SCRIPT_DIR}/pwd_cli.py --listen"

# Universal Speech Synthesis (TTS) Aliases
v-speak() {
    if [ $# -gt 0 ]; then
        "${PYTHON_BIN}" "${SCRIPT_DIR}/pwd_cli.py" --speak "$*"
    else
        "${PYTHON_BIN}" "${SCRIPT_DIR}/pwd_cli.py" --speak "-"
    fi
}

v-read() {
    "${PYTHON_BIN}" "${SCRIPT_DIR}/pwd_cli.py" --speak-file "$1"
}

alias v-stop="${PYTHON_BIN} ${SCRIPT_DIR}/pwd_cli.py --stop-speech"
alias v-manual="${PYTHON_BIN} ${SCRIPT_DIR}/manual_launcher.py"
alias v-settings="${PYTHON_BIN} ${SCRIPT_DIR}/config_web_launcher.py"
alias v-dash="${PYTHON_BIN} ${SCRIPT_DIR}/dashboard_launcher.py"

# Voice command prompt injector
voice-cmd() {
    local text
    text=$("${PYTHON_BIN}" "${SCRIPT_DIR}/pwd_cli.py" --listen --pipe)
    if [ -n "${text}" ]; then
        if [ -n "${BASH_VERSION}" ]; then
            # Inject directly into readline buffer in Bash
            READLINE_LINE="${text}"
            READLINE_POINT=${#text}
        elif [ -n "${ZSH_VERSION}" ]; then
            # Inject directly into ZLE buffer in Zsh
            BUFFER="${text}"
            CURSOR=${#text}
        else
            echo "${text}"
        fi
    fi
}

# Optional interactive keybinding (Ctrl+G) for interactive Bash prompts
if [[ $- == *i* ]]; then
    if [ -n "${BASH_VERSION}" ]; then
        bind -x '"\C-g": voice-cmd' 2>/dev/null || true
    fi
fi
