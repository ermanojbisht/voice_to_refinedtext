"""Shared UI colour palette — Catppuccin Mocha (refined).

Import this module in any GUI file instead of copy-pasting the constants:

    from theme import BG, SURFACE, OVERLAY, TEXT, SUBTLE, MUTED, ACCENT, GREEN, RED, YELLOW
"""

BG      = "#1e1e2e"   # base background
SURFACE = "#2a2b3d"   # card / panel background (was #313244 — slightly deeper)
OVERLAY = "#45475a"   # hover, chip, clip row background
FIELD   = "#181825"   # dark well for text entries, comboboxes, and textboxes
BORDER  = "#363a4f"   # card and field outline border
TEXT    = "#cdd6f4"   # primary readable text
SUBTLE  = "#e0eddd"   # secondary text — readable on dark bg (Catppuccin Subtext1)
MUTED   = "#6c7086"   # dim / inactive text (old SUBTLE — use sparingly)
ACCENT  = "#89b4fa"   # blue highlights, headers, active step
PRIMARY = "#89b4fa"   # primary action button fill
PRIMARY_HOVER = "#b4befe"  # primary hover fill
GREEN   = "#a6e3a1"   # success, saved, ok states
RED     = "#f38ba8"   # error, delete, recording indicator
YELLOW  = "#f9e2af"   # warning, synthesis in-progress

