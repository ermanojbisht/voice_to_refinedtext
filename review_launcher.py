#!/usr/bin/env python3
"""Desktop launcher for the Executive Evening Review Web Studio.

Detects installed browsers and opens http://127.0.0.1:8765/review as an independent,
frameless desktop application window with zero X11/Wayland canvas lag.
"""
import os
import sys
import shutil
import subprocess
import webbrowser
import time
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import settings_server

DEFAULT_PORT = 8765


def is_server_ready(port: int = None) -> bool:
    if port is None:
        port = settings_server.get_configured_port()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.6) as r:
            return r.status == 200
    except Exception:
        return False


def launch_review_app(port: int = None, date_str: str = None):
    if port is None:
        port = settings_server.get_configured_port()

    # Ensure daemon is running
    if not is_server_ready(port):
        settings_server.start_server_daemon(port)
        for _ in range(15):
            if is_server_ready(port):
                break
            time.sleep(0.05)

    # Initialize review if date specified
    if date_str:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/review/start",
                data=f'{{"date": "{date_str}"}}'.encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=1.0)
        except Exception:
            pass

    url = f"http://127.0.0.1:{port}/review"

    # Search for Chromium-based browsers that support standalone --app mode
    candidate_browsers = [
        "google-chrome",
        "google-chrome-stable",
        "microsoft-edge",
        "brave-browser",
        "chromium-browser",
        "chromium",
    ]

    for browser_name in candidate_browsers:
        bin_path = shutil.which(browser_name)
        if bin_path:
            cmd = [
                bin_path,
                f"--app={url}",
                "--window-size=1200,820",
                f"--user-data-dir={os.path.expanduser('~/.cache/voice_refiner_review_app')}",
            ]
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                pass

    # Fallback to default browser
    webbrowser.open(url)


if __name__ == "__main__":
    launch_review_app()
