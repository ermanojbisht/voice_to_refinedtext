#!/usr/bin/env python3
"""Unified Self-Healing Diagnostic & Environment Doctor for Voice-to-RefinedText.

Inspects all 6 critical runtime subsystems:
1. Python Runtime & Core Libraries
2. ASR Models, MODELS_DIR & Discovery Tiers
3. Audio Input/Output Hardware & Mic Signal
4. Desktop Environment, Wayland/X11 & Evdev Hotkeys
5. Ollama LLM Service & Refinement Models
6. Audio-to-Idea Batch Processing & External Tools

Usage:
    python doctor.py           # Standard diagnostic check
    python doctor.py --json    # Machine-readable JSON output
    python doctor.py --mic     # Live 1.5s microphone signal probe
    python doctor.py --fix     # Interactive auto-fix for safe issues
"""
from __future__ import annotations

import argparse
import grp
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Base Project Root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@dataclass
class CheckResult:
    category: str
    name: str
    status: str  # "PASS", "WARN", "FAIL"
    message: str
    details: Optional[str] = None
    remediation_cmd: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class DoctorReport:
    overall_status: str  # "PASS", "WARN", "FAIL"
    timestamp: float
    platform: str
    python_version: str
    checks: List[CheckResult] = field(default_factory=list)
    remediations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "timestamp": self.timestamp,
            "platform": self.platform,
            "python_version": self.python_version,
            "checks": [asdict(c) for c in self.checks],
            "remediations": self.remediations,
        }


# ============================================================================
# Check Engine Implementations
# ============================================================================

def _load_app_config() -> Dict[str, Any]:
    cfg_path = os.path.join(PROJECT_ROOT, "config.json")
    if os.path.isfile(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def check_python_environment() -> List[CheckResult]:
    results = []
    # 1. Python version
    py_ver = sys.version_info
    ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    if py_ver.major >= 3 and py_ver.minor >= 10:
        results.append(CheckResult(
            category="Python Environment",
            name="Python Version",
            status="PASS",
            message=f"Python {ver_str} (>= 3.10 supported)",
        ))
    else:
        results.append(CheckResult(
            category="Python Environment",
            name="Python Version",
            status="FAIL",
            message=f"Python {ver_str} is outdated. Python 3.10+ required.",
            remediation_cmd="sudo apt install python3.10 python3.10-venv",
        ))

    # 2. Critical libraries
    critical_libs = [
        ("numpy", "Core numerical processing"),
        ("sounddevice", "Microphone audio capture"),
        ("scipy", "WAV processing & signal handling"),
        ("evdev", "Kernel-level hardware hotkey listener"),
        ("requests", "Ollama LLM REST client"),
    ]
    for mod_name, desc in critical_libs:
        try:
            mod = __import__(mod_name)
            m_ver = getattr(mod, "__version__", "installed")
            results.append(CheckResult(
                category="Python Environment",
                name=f"Module: {mod_name}",
                status="PASS",
                message=f"{desc} (v{m_ver})",
            ))
        except ImportError:
            results.append(CheckResult(
                category="Python Environment",
                name=f"Module: {mod_name}",
                status="FAIL",
                message=f"Missing required library: {mod_name} ({desc})",
                remediation_cmd=f"pip install {mod_name}",
                auto_fixable=True,
            ))

    # 3. ASR Backends
    has_transcribe_cpp = False
    try:
        import transcribe_cpp  # noqa: F401
        has_transcribe_cpp = True
        results.append(CheckResult(
            category="Python Environment",
            name="Engine: transcribe_cpp",
            status="PASS",
            message="GGML Vulkan / CUDA engine installed (~50x real-time)",
        ))
    except (ImportError, Exception):
        results.append(CheckResult(
            category="Python Environment",
            name="Engine: transcribe_cpp",
            status="WARN",
            message="transcribe-cpp bindings not installed. System will use faster-whisper fallback.",
            remediation_cmd="pip install transcribe-cpp",
        ))

    try:
        import faster_whisper  # noqa: F401
        results.append(CheckResult(
            category="Python Environment",
            name="Engine: faster_whisper",
            status="PASS",
            message="CTranslate2 Whisper runtime available",
        ))
    except ImportError:
        status = "FAIL" if not has_transcribe_cpp else "WARN"
        results.append(CheckResult(
            category="Python Environment",
            name="Engine: faster_whisper",
            status=status,
            message="faster-whisper is not installed.",
            remediation_cmd="pip install faster-whisper",
            auto_fixable=True,
        ))

    return results


def check_models_and_portability(config: Dict[str, Any]) -> List[CheckResult]:
    results = []
    models_dir = config.get("MODELS_DIR")
    presets = config.get("ASR_PRESETS", {})

    # Try to import resolver
    try:
        from audio_to_idea.asr.factory import resolve_model_path
    except Exception:
        def resolve_model_path(path_or_name, models_dir=None, default_filename=None):
            fname = os.path.basename(path_or_name or default_filename or "")
            dirs = [models_dir, os.path.join(PROJECT_ROOT, "models"), "/media/manoj/F1/models-handy"]
            for d in dirs:
                if d and os.path.isfile(os.path.join(d, fname)):
                    return os.path.join(d, fname)
            return path_or_name

    # Check MODELS_DIR
    if models_dir:
        exp_dir = os.path.expanduser(models_dir)
        if os.path.isdir(exp_dir):
            file_count = len([f for f in os.listdir(exp_dir) if f.endswith((".gguf", ".bin"))])
            results.append(CheckResult(
                category="Models & Portability",
                name="MODELS_DIR Path",
                status="PASS",
                message=f"Configured directory exists with {file_count} model file(s): {exp_dir}",
            ))
        else:
            results.append(CheckResult(
                category="Models & Portability",
                name="MODELS_DIR Path",
                status="WARN",
                message=f"Configured MODELS_DIR does not exist on this PC: {models_dir}",
                remediation_cmd=f"mkdir -p {exp_dir} # or update MODELS_DIR in config.json",
                auto_fixable=True,
            ))
    else:
        results.append(CheckResult(
            category="Models & Portability",
            name="MODELS_DIR Path",
            status="WARN",
            message="MODELS_DIR not explicitly set in config.json. Using standard fallback tiers.",
            remediation_cmd='Add "MODELS_DIR": "./models" to config.json',
        ))

    # Check Local ./models/ directory
    local_models_dir = os.path.join(PROJECT_ROOT, "models")
    if os.path.isdir(local_models_dir):
        local_count = len([f for f in os.listdir(local_models_dir) if f.endswith((".gguf", ".bin"))])
        results.append(CheckResult(
            category="Models & Portability",
            name="Local ./models/ Directory",
            status="PASS",
            message=f"Zero-config drop-in folder exists with {local_count} model(s).",
        ))
    else:
        results.append(CheckResult(
            category="Models & Portability",
            name="Local ./models/ Directory",
            status="WARN",
            message="Local ./models/ folder does not exist. (Recommended for portable multi-PC drop-in).",
            remediation_cmd=f"mkdir -p {local_models_dir}",
            auto_fixable=True,
        ))

    # Check ASR Presets
    for pkey, pinfo in presets.items():
        backend = pinfo.get("backend", "faster_whisper")
        label = pinfo.get("label", pkey)
        raw_model = pinfo.get("model", "")

        if backend == "transcribe_cpp":
            resolved = resolve_model_path(raw_model, models_dir=models_dir)
            if os.path.isfile(resolved):
                size_mb = os.path.getsize(resolved) / (1024 * 1024)
                results.append(CheckResult(
                    category="Models & Portability",
                    name=f"Preset: {label}",
                    status="PASS",
                    message=f"Model resolved ({size_mb:.1f} MB): {resolved}",
                ))
            else:
                results.append(CheckResult(
                    category="Models & Portability",
                    name=f"Preset: {label}",
                    status="FAIL",
                    message=f"Model file not found: {raw_model}. Resolved to: {resolved}",
                    remediation_cmd=f"Copy {os.path.basename(raw_model)} into {models_dir or local_models_dir}",
                ))
        elif backend == "faster_whisper":
            results.append(CheckResult(
                category="Models & Portability",
                name=f"Preset: {label}",
                status="PASS",
                message=f"Faster-Whisper profile configured for: {raw_model}",
            ))

    # Check Kokoro TTS Neural Speech Models
    try:
        from pwd_helper.tts.backends.kokoro_backend import KokoroBackend
        kokoro_backend = KokoroBackend()
        m_file, v_file = kokoro_backend._find_model_paths(config)
        if m_file and v_file:
            results.append(CheckResult(
                category="Models & Portability",
                name="Kokoro TTS Models",
                status="PASS",
                message=f"Neural TTS ready: {os.path.basename(m_file)} and {os.path.basename(v_file)}",
            ))
        else:
            results.append(CheckResult(
                category="Models & Portability",
                name="Kokoro TTS Models",
                status="WARN",
                message="Kokoro model (kokoro-v1.0.onnx) or voices-v1.0.bin not found in standard paths.",
                remediation_cmd=f"mkdir -p {local_models_dir}/kokoro-models && cp /path/to/kokoro-models/* {local_models_dir}/kokoro-models/",
            ))
    except Exception as exc:
        results.append(CheckResult(
            category="Models & Portability",
            name="Kokoro TTS Models",
            status="WARN",
            message=f"Could not verify Kokoro TTS: {exc}",
        ))

    return results


def check_audio_hardware(run_mic_probe: bool = False) -> List[CheckResult]:
    results = []
    try:
        import sounddevice as sd
    except ImportError:
        results.append(CheckResult(
            category="Audio Hardware",
            name="Audio Driver (sounddevice)",
            status="FAIL",
            message="sounddevice library missing.",
            remediation_cmd="pip install sounddevice",
        ))
        return results

    try:
        devices = sd.query_devices()
        default_in = sd.default.device[0]
        default_out = sd.default.device[1]

        if default_in is not None and default_in >= 0:
            in_info = sd.query_devices(default_in)
            results.append(CheckResult(
                category="Audio Hardware",
                name="Default Microphone",
                status="PASS",
                message=f"[{default_in}] {in_info.get('name')} (Max inputs: {in_info.get('max_input_channels')})",
            ))
        else:
            results.append(CheckResult(
                category="Audio Hardware",
                name="Default Microphone",
                status="FAIL",
                message="No default input/recording audio device detected.",
                remediation_cmd="Check system audio settings or plug in a microphone.",
            ))

        if default_out is not None and default_out >= 0:
            out_info = sd.query_devices(default_out)
            results.append(CheckResult(
                category="Audio Hardware",
                name="Default Speaker",
                status="PASS",
                message=f"[{default_out}] {out_info.get('name')}",
            ))
        else:
            results.append(CheckResult(
                category="Audio Hardware",
                name="Default Speaker",
                status="WARN",
                message="No default audio output device found. Chimes will be muted.",
            ))

        # Optional active mic probe
        if run_mic_probe:
            import numpy as np
            print("🎤 Probing microphone for 1.5 seconds... Please speak into mic:")
            duration = 1.5
            sr = 16000
            recording = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
            sd.wait()
            rms = float(np.sqrt(np.mean(np.square(recording))) * 32768.0)
            if rms > 150.0:
                results.append(CheckResult(
                    category="Audio Hardware",
                    name="Live Mic Signal Test",
                    status="PASS",
                    message=f"Signal verified (Audio RMS: {rms:.1f} / 32768).",
                ))
            elif rms > 40.0:
                results.append(CheckResult(
                    category="Audio Hardware",
                    name="Live Mic Signal Test",
                    status="WARN",
                    message=f"Low signal detected (Audio RMS: {rms:.1f}). Microphone may be quiet.",
                ))
            else:
                results.append(CheckResult(
                    category="Audio Hardware",
                    name="Live Mic Signal Test",
                    status="FAIL",
                    message=f"Zero audio captured (Audio RMS: {rms:.1f}). Microphone appears muted or wrong input selected.",
                    remediation_cmd="Unmute microphone in OS sound settings or select proper default input device.",
                ))

    except Exception as exc:
        results.append(CheckResult(
            category="Audio Hardware",
            name="Audio Device Query",
            status="FAIL",
            message=f"Audio system error: {exc}",
            remediation_cmd="Ensure ALSA / PulseAudio / PipeWire is running.",
        ))

    return results


def check_desktop_and_hotkeys() -> List[CheckResult]:
    results = []
    # 1. Wayland vs X11
    session_type = os.environ.get("XDG_SESSION_TYPE", "")
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    is_wayland = (session_type.lower() == "wayland") or bool(wayland_display)

    display_name = "Wayland" if is_wayland else ("X11" if os.environ.get("DISPLAY") else "Headless")
    results.append(CheckResult(
        category="Desktop & Hotkeys",
        name="Display Server",
        status="PASS",
        message=f"Detected: {display_name} (Session: {session_type or 'unknown'})",
    ))

    # 2. Evdev Kernel Hotkey Permissions
    user_name = os.environ.get("USER", os.environ.get("LOGNAME", ""))
    in_input_group = False
    try:
        user_groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
        in_input_group = "input" in user_groups
    except Exception:
        pass

    # Test actual access to /dev/input
    dev_input = Path("/dev/input")
    readable_events = 0
    if dev_input.is_dir():
        for ev in dev_input.glob("event*"):
            if os.access(ev, os.R_OK):
                readable_events += 1

    if readable_events > 0:
        results.append(CheckResult(
            category="Desktop & Hotkeys",
            name="Evdev Walkie-Talkie Hotkeys",
            status="PASS",
            message=f"Kernel event access verified ({readable_events} readable keyboard/input devices).",
        ))
    else:
        results.append(CheckResult(
            category="Desktop & Hotkeys",
            name="Evdev Walkie-Talkie Hotkeys",
            status="WARN",
            message="No read permission for /dev/input/event*. Walkie-Talkie will use pynput fallback.",
            remediation_cmd=f"sudo usermod -a -G input {user_name} && echo 'Log out and log back in to apply.'",
        ))

    # 3. Auto-Paste Tools
    if is_wayland:
        ydotool_bin = shutil.which("ydotool")
        ydotoold_socket = Path(os.environ.get("YDOTOOL_SOCKET", "/tmp/.ydotool_socket")).exists()
        wl_copy = shutil.which("wl-copy")

        if ydotool_bin and ydotoold_socket:
            results.append(CheckResult(
                category="Desktop & Hotkeys",
                name="Auto-Paste (Wayland)",
                status="PASS",
                message="ydotool + active ydotoold daemon socket ready for direct typing.",
            ))
        elif wl_copy:
            results.append(CheckResult(
                category="Desktop & Hotkeys",
                name="Auto-Paste (Wayland)",
                status="PASS",
                message="wl-copy / wl-paste available (clipboard restore mode active).",
            ))
        else:
            results.append(CheckResult(
                category="Desktop & Hotkeys",
                name="Auto-Paste (Wayland)",
                status="WARN",
                message="Neither ydotool daemon nor wl-copy found on Wayland.",
                remediation_cmd="sudo apt install wl-clipboard ydotool",
            ))
    else:
        xdotool_bin = shutil.which("xdotool")
        xclip_bin = shutil.which("xclip")
        if xdotool_bin and xclip_bin:
            results.append(CheckResult(
                category="Desktop & Hotkeys",
                name="Auto-Paste (X11)",
                status="PASS",
                message="xdotool + xclip ready for seamless paste and restore.",
            ))
        else:
            results.append(CheckResult(
                category="Desktop & Hotkeys",
                name="Auto-Paste (X11)",
                status="WARN",
                message="Missing xdotool or xclip for X11 clipboard operations.",
                remediation_cmd="sudo apt install xdotool xclip",
            ))

    return results


def check_ollama_service(config: Dict[str, Any]) -> List[CheckResult]:
    results = []
    host = config.get("OLLAMA_HOST", "http://localhost:11434")
    en_model = config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")
    hi_model = config.get("OLLAMA_MODELS", {}).get("hi", "llama3-hindi")

    import urllib.request
    import urllib.error

    tags_url = f"{host.rstrip('/')}/api/tags"
    installed_models: List[str] = []

    try:
        req = urllib.request.Request(tags_url, headers={"User-Agent": "VoiceDoctor/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("models", []):
                    m_name = m.get("name", "")
                    if m_name:
                        installed_models.append(m_name)
                results.append(CheckResult(
                    category="Ollama LLM Service",
                    name="Ollama Service Reachability",
                    status="PASS",
                    message=f"Online at {host} ({len(installed_models)} models pulled).",
                ))
            else:
                results.append(CheckResult(
                    category="Ollama LLM Service",
                    name="Ollama Service Reachability",
                    status="FAIL",
                    message=f"HTTP {resp.status} received from {tags_url}",
                    remediation_cmd="systemctl start ollama || ollama serve",
                ))
    except Exception as exc:
        results.append(CheckResult(
            category="Ollama LLM Service",
            name="Ollama Service Reachability",
            status="FAIL",
            message=f"Cannot connect to Ollama at {host}: {exc}",
            remediation_cmd="ollama serve",
        ))
        return results

    # Check English Model
    en_match = any(m.startswith(en_model.split(":")[0]) for m in installed_models)
    if en_match:
        results.append(CheckResult(
            category="Ollama LLM Service",
            name=f"English Refiner ({en_model})",
            status="PASS",
            message=f"Model found in Ollama repository.",
        ))
    else:
        results.append(CheckResult(
            category="Ollama LLM Service",
            name=f"English Refiner ({en_model})",
            status="FAIL",
            message=f"Model '{en_model}' is not pulled in Ollama.",
            remediation_cmd=f"ollama pull {en_model}",
            auto_fixable=True,
        ))

    # Check Hindi Model
    hi_match = any(m.startswith(hi_model.split(":")[0]) for m in installed_models)
    if hi_match:
        results.append(CheckResult(
            category="Ollama LLM Service",
            name=f"Hindi Refiner ({hi_model})",
            status="PASS",
            message=f"Model found in Ollama repository.",
        ))
    else:
        results.append(CheckResult(
            category="Ollama LLM Service",
            name=f"Hindi Refiner ({hi_model})",
            status="WARN",
            message=f"Hindi model '{hi_model}' is not pulled. Hindi translation will fall back to English model.",
            remediation_cmd=f"ollama pull {hi_model}",
            auto_fixable=True,
        ))

    return results


def check_batch_and_cli_tools() -> List[CheckResult]:
    results = []
    # 1. ffmpeg / ffprobe
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    if ffmpeg and ffprobe:
        results.append(CheckResult(
            category="Batch & Media Tools",
            name="FFmpeg & FFprobe",
            status="PASS",
            message=f"Media transcoding tools detected: {ffmpeg}",
        ))
    else:
        results.append(CheckResult(
            category="Batch & Media Tools",
            name="FFmpeg & FFprobe",
            status="FAIL",
            message="ffmpeg/ffprobe not found. Required for decoding audio containers (m4a, ogg, flac, mp3).",
            remediation_cmd="sudo apt install ffmpeg",
        ))

    return results


# ============================================================================
# Diagnostic Orchestration & Formatting
# ============================================================================

def run_all_checks(run_mic: bool = False) -> DoctorReport:
    config = _load_app_config()
    all_checks: List[CheckResult] = []

    all_checks.extend(check_python_environment())
    all_checks.extend(check_models_and_portability(config))
    all_checks.extend(check_audio_hardware(run_mic_probe=run_mic))
    all_checks.extend(check_desktop_and_hotkeys())
    all_checks.extend(check_ollama_service(config))
    all_checks.extend(check_batch_and_cli_tools())

    # Overall Status calculation
    has_fail = any(c.status == "FAIL" for c in all_checks)
    has_warn = any(c.status == "WARN" for c in all_checks)
    overall = "FAIL" if has_fail else ("WARN" if has_warn else "PASS")

    # Collect distinct remediation commands
    remediations: List[str] = []
    for c in all_checks:
        if c.remediation_cmd and c.remediation_cmd not in remediations:
            remediations.append(c.remediation_cmd)

    return DoctorReport(
        overall_status=overall,
        timestamp=time.time(),
        platform=sys.platform,
        python_version=sys.version.split()[0],
        checks=all_checks,
        remediations=remediations,
    )


# Color formatting for terminal
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_GREEN = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_RED = "\033[91m"
CLR_CYAN = "\033[96m"
CLR_GRAY = "\033[90m"


def print_terminal_report(report: DoctorReport):
    print(f"\n{CLR_BOLD}{CLR_CYAN}======================================================================{CLR_RESET}")
    print(f"{CLR_BOLD}  🏥 UNIFIED VOICE-TO-REFINEDTEXT DIAGNOSTIC DOCTOR{CLR_RESET}")
    print(f"{CLR_GRAY}  Platform: {report.platform} | Python: {report.python_version} | Status: {report.overall_status}{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_CYAN}======================================================================{CLR_RESET}\n")

    current_cat = None
    for c in report.checks:
        if c.category != current_cat:
            current_cat = c.category
            print(f"{CLR_BOLD}▶ {current_cat}{CLR_RESET}")

        if c.status == "PASS":
            badge = f"{CLR_GREEN}[PASS]{CLR_RESET}"
        elif c.status == "WARN":
            badge = f"{CLR_YELLOW}[WARN]{CLR_RESET}"
        else:
            badge = f"{CLR_RED}[FAIL]{CLR_RESET}"

        print(f"  {badge} {CLR_BOLD}{c.name:<32}{CLR_RESET} {c.message}")
        if c.remediation_cmd:
            print(f"         {CLR_GRAY}↳ Fix:{CLR_RESET} {CLR_YELLOW}{c.remediation_cmd}{CLR_RESET}")
    print()

    # Overall Summary
    print(f"{CLR_BOLD}{CLR_CYAN}----------------------------------------------------------------------{CLR_RESET}")
    if report.overall_status == "PASS":
        print(f"  {CLR_BOLD}{CLR_GREEN}✅ ALL SUBSYSTEMS HEALTHY — Application is ready for high-speed use!{CLR_RESET}")
    elif report.overall_status == "WARN":
        print(f"  {CLR_BOLD}{CLR_YELLOW}⚠️  SYSTEM OPERATIONAL WITH WARNINGS — Review recommendations above.{CLR_RESET}")
    else:
        print(f"  {CLR_BOLD}{CLR_RED}❌ CRITICAL ISSUES DETECTED — Execute the fixes below to heal system.{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_CYAN}----------------------------------------------------------------------{CLR_RESET}")

    if report.remediations:
        print(f"\n{CLR_BOLD}🔧 One-Liner Self-Healing Action Commands:{CLR_RESET}")
        for i, cmd in enumerate(report.remediations, 1):
            print(f"  {i}. {CLR_YELLOW}{cmd}{CLR_RESET}")
        print()


def run_auto_fixes(report: DoctorReport):
    """Executes safe auto-fixes with user confirmation."""
    auto_fixes = [c for c in report.checks if c.auto_fixable and c.remediation_cmd]
    if not auto_fixes:
        print("No automatic fixes available. Please review manual instructions.")
        return

    print(f"\nFound {len(auto_fixes)} auto-fixable issue(s):")
    for f in auto_fixes:
        print(f"  - {f.name}: {f.remediation_cmd}")

    resp = input("\nExecute these fixes now? (y/N): ").strip().lower()
    if resp != "y":
        print("Fixes aborted.")
        return

    for f in auto_fixes:
        print(f"\n⚙️ Running: {f.remediation_cmd} ...")
        res = subprocess.run(f.remediation_cmd, shell=True)
        if res.returncode == 0:
            print(f"✅ Fixed: {f.name}")
        else:
            print(f"❌ Failed to run fix for {f.name} (exit code {res.returncode})")


def main():
    parser = argparse.ArgumentParser(description="Unified Self-Healing Diagnostic Doctor")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--mic", action="store_true", help="Probe microphone signal actively for 1.5 seconds")
    parser.add_argument("--fix", action="store_true", help="Interactively run safe automated fixes")
    args = parser.parse_args()

    report = run_all_checks(run_mic=args.mic)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_terminal_report(report)
        if args.fix:
            run_auto_fixes(report)

    sys.exit(0 if report.overall_status in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
