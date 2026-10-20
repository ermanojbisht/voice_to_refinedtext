"""Live Rich Terminal Dictation HUD.

Provides an animated, interactive Heads-Up Display (HUD) in the terminal
showing real-time microphone VU level metering, VAD status, and pipeline stages.

Features:
- Pure terminal rendering using rich (Live, Panel, Text, Table).
- Automatic TTY and pipe detection: separates visual HUD (stderr) from clean text output (stdout)
  so commands like `pwd_cli.py --listen | git commit -F -` work seamlessly without ANSI corruption.
- Real-time RMS audio energy gauge callback.
- Graceful plain-text fallback if rich is missing or if --no-hud is passed.
- Completely isolated: zero side effects on desktop tray app or background hotkey daemon.

Compatible with Python 3.10 through 3.14.
"""
from __future__ import annotations

import sys
import time
from typing import Optional, Sequence

# Graceful optional rich import
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class TerminalHUD:
    """Manages the in-terminal live dictation HUD."""

    def __init__(
        self,
        enabled: bool = True,
        pipe_mode: Optional[bool] = None,
        preset_label: str = "Smart Bilingual",
        goal_label: str = "Official English",
    ) -> None:
        self.enabled = enabled and HAS_RICH
        if pipe_mode is not None:
            self.pipe_mode = pipe_mode
        else:
            self.pipe_mode = not sys.stdout.isatty()
        self.preset_label = preset_label
        self.goal_label = goal_label

        self.state = "IDLE"
        self.current_rms = 0.0
        self.max_rms = 1800.0  # Normalized ceiling for standard mic speech
        self.spoken_preview = ""
        self.status_detail = ""

        self._console: Optional[Console] = None
        self._live: Optional[Live] = None

        if self.enabled:
            # Direct HUD rendering to stderr so stdout remains 100% pipe-clean
            self._console = Console(stderr=True)

    def _build_renderable(self):
        """Constructs the Rich Panel showing state, live VU bar, and metadata."""
        if not HAS_RICH:
            return ""

        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold cyan", width=12)
        table.add_column()

        # 1. State indicator
        if self.state == "RECORDING":
            state_text = Text("● RECORDING (Live Mic Active)", style="bold red")
        elif self.state == "TRANSCRIBING":
            state_text = Text("🧠 TRANSCRIBING...", style="bold yellow")
        elif self.state == "REFINING":
            state_text = Text("⚡ REFINING & CORRECTING...", style="bold magenta")
        elif self.state == "DONE":
            state_text = Text("✔ COMPLETE", style="bold green")
        else:
            state_text = Text("○ IDLE", style="dim")
        table.add_row("Status:", state_text)

        # 2. Live Audio VU Meter (active during recording)
        if self.state == "RECORDING":
            ratio = min(1.0, max(0.0, self.current_rms / self.max_rms))
            total_bars = 28
            filled = int(ratio * total_bars)
            unfilled = total_bars - filled

            # Color gradient: green -> yellow -> red
            bar_text = Text()
            for idx in range(filled):
                if idx < 16:
                    bar_text.append("█", style="green")
                elif idx < 22:
                    bar_text.append("█", style="yellow")
                else:
                    bar_text.append("█", style="bold red")
            bar_text.append("░" * unfilled, style="dim")

            pct = int(ratio * 100)
            level_desc = "Good Signal" if pct > 15 else "Silence / Low"
            table.add_row("Mic VU:", Text.assemble(bar_text, f"  {pct:2d}% ({level_desc})"))

        # 3. Configuration Metadata
        table.add_row("Preset:", Text(self.preset_label, style="bold white"))
        table.add_row("Refinement:", Text(self.goal_label, style="cyan"))

        if self.status_detail:
            table.add_row("Note:", Text(self.status_detail, style="italic yellow"))

        return Panel(
            table,
            title="[bold yellow]🎙️  AI Voice Refiner — Terminal HUD[/bold yellow]",
            subtitle="[dim]Press Hotkey or Stop Speaking to Finish[/dim]",
            border_style="bright_blue",
            padding=(1, 2),
        )

    def start_listening(self, preset_label: Optional[str] = None, goal_label: Optional[str] = None):
        """Starts live microphone HUD session."""
        if preset_label:
            self.preset_label = preset_label
        if goal_label:
            self.goal_label = goal_label

        self.state = "RECORDING"
        self.current_rms = 0.0

        if self.enabled and self._console:
            self._live = Live(
                self._build_renderable(),
                console=self._console,
                refresh_per_second=15,
                transient=True,
            )
            self._live.start()
        else:
            sys.stderr.write(f"🎙️  Listening... Speak now ({self.preset_label})\n")
            sys.stderr.flush()

    def update_audio(self, chunk, energy=None):
        """Callback invoked on each PCM audio block."""
        if energy is not None:
            try:
                self.current_rms = float(energy)
            except Exception:
                pass
        elif chunk is not None:
            # Approximate RMS from raw bytes or numpy array
            try:
                import numpy as np
                if isinstance(chunk, bytes):
                    arr = np.frombuffer(chunk, dtype=np.int16)
                else:
                    arr = np.asarray(chunk)
                if len(arr) > 0:
                    self.current_rms = float(np.sqrt(np.mean(arr.astype(float) ** 2)))
            except Exception:
                pass

        if self._live:
            self._live.update(self._build_renderable())

    def set_state(self, state: str, detail: str = ""):
        """Transitions state (e.g. TRANSCRIBING, REFINING)."""
        self.state = state
        self.status_detail = detail
        if self._live:
            self._live.update(self._build_renderable())
        elif not self.enabled:
            sys.stderr.write(f"  [{state}] {detail}\n")
            sys.stderr.flush()

    def finish(self, text: str):
        """Closes HUD cleanly and prints final summary."""
        self.state = "DONE"
        if self._live:
            self._live.stop()
            self._live = None

        if not self.pipe_mode and self._console and self.enabled:
            # Print elegant summary panel in interactive TTY mode
            summary = Table.grid(padding=(0, 1))
            summary.add_column(style="bold green", width=12)
            summary.add_column()
            summary.add_row("Refined:", Text(text, style="bold white"))
            self._console.print(
                Panel(summary, title="[bold green]✔ Transcription Finished[/bold green]", border_style="green")
            )
        elif not self.enabled and not self.pipe_mode:
            sys.stderr.write(f"✔ Result: {text}\n")
            sys.stderr.flush()

    def close(self):
        """Ensures any live display is stopped."""
        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None
