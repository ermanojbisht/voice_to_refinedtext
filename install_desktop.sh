#!/bin/bash
# Installs .desktop launchers for AI Voice Refiner and Evening Review
# into ~/.local/share/applications/ (visible in GNOME app drawer).
# Run once after installation: bash install_desktop.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

mkdir -p "$APPS_DIR" "$ICONS_DIR"

# ── Generate icons (simple coloured SVG → PNG via ImageMagick or Python) ──────

generate_icon() {
    local name="$1"
    local color="$2"
    local label="$3"
    local out="$ICONS_DIR/${name}.png"

    if command -v magick &>/dev/null; then
        magick -size 256x256 xc:"$color" \
            -fill white -font DejaVu-Sans-Bold -pointsize 80 \
            -gravity Center -annotate 0 "$label" \
            "$out"
    elif command -v convert &>/dev/null; then
        convert -size 256x256 xc:"$color" \
            -fill white -font DejaVu-Sans-Bold -pointsize 80 \
            -gravity Center -annotate 0 "$label" \
            "$out"
    else
        # Fallback: generate via Python Pillow (already installed as project dep)
        "$VENV_PYTHON" - <<PYEOF
from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGBA", (256, 256), "$color")
draw = ImageDraw.Draw(img)
try:
    fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
except Exception:
    fnt = ImageFont.load_default()
text = "$label"
bbox = draw.textbbox((0, 0), text, font=fnt)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((256 - tw) // 2, (256 - th) // 2), text, fill="white", font=fnt)
img.save("$out")
PYEOF
    fi
    echo "  Icon: $out"
}

echo "Generating icons..."
generate_icon "ai-voice-refiner" "#45475a" "Mic"
generate_icon "ai-evening-review" "#a6e3a1" "Eve"

gtk-update-icon-cache --quiet --ignore-theme-index "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# ── AI Voice Refiner Tray ─────────────────────────────────────────────────────

cat > "$APPS_DIR/ai-voice-refiner.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AI Voice Refiner
GenericName=Voice to Text Tray
Comment=Local AI voice refiner — Ctrl+Alt+V to record
Exec=$VENV_PYTHON $SCRIPT_DIR/tray_app.py
Icon=ai-voice-refiner
Terminal=false
Categories=Utility;AudioVideo;
Keywords=voice;transcribe;ollama;ai;
StartupNotify=false
EOF

echo "Installed: AI Voice Refiner  →  $APPS_DIR/ai-voice-refiner.desktop"

# ── Evening Review Dashboard ──────────────────────────────────────────────────

cat > "$APPS_DIR/ai-evening-review.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Evening Review
GenericName=Daily Evening Review
Comment=Guided evening journal review powered by local AI
Exec=$VENV_PYTHON $SCRIPT_DIR/review_dashboard.py
Icon=ai-evening-review
Terminal=false
Categories=Utility;Office;
Keywords=journal;review;evening;notes;obsidian;ai;
StartupNotify=false
EOF

echo "Installed: Evening Review  →  $APPS_DIR/ai-evening-review.desktop"

# Refresh app cache
update-desktop-database "$APPS_DIR" 2>/dev/null || true

echo ""
echo "Done! Both launchers are now in your GNOME app drawer."
echo "Search 'Voice Refiner' or 'Evening Review'."
echo ""
echo "Note: Evening Review opened directly (without the tray) starts the"
echo "      dashboard standalone — use the tray for full review workflow."
