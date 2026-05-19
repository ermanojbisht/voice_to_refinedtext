#!/usr/bin/env bash
# Install the Morning Brief as a systemd user timer.
# Run once: bash install_morning_brief.sh
# Re-run after changing morning_briefing_time in review_config.json.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_DIR="$HOME/.config/systemd/user"
PYTHON="$(which python3)"

mkdir -p "$SERVICE_DIR"

# Read configured time from review_config.json (default 08:00)
BRIEF_TIME="$($PYTHON -c "
import json, sys
try:
    with open('$SCRIPT_DIR/review_config.json') as f:
        cfg = json.load(f)
    print(cfg.get('morning_briefing_time', '08:00'))
except Exception:
    print('08:00')
")"

echo "Installing Morning Brief timer for $BRIEF_TIME daily..."

cat > "$SERVICE_DIR/morning-brief.service" << EOF
[Unit]
Description=AI Voice Refiner — Morning Priority Brief

[Service]
Type=oneshot
ExecStart=$PYTHON $SCRIPT_DIR/morning_brief.py
Environment=DISPLAY=:1
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus
EOF

cat > "$SERVICE_DIR/morning-brief.timer" << EOF
[Unit]
Description=AI Voice Refiner — Morning Brief Timer

[Timer]
OnCalendar=*-*-* ${BRIEF_TIME}:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now morning-brief.timer

echo ""
echo "Done. Morning Brief will run daily at $BRIEF_TIME."
echo ""
echo "Useful commands:"
echo "  systemctl --user status morning-brief.timer    # check next trigger"
echo "  systemctl --user status morning-brief.service  # check last run"
echo "  systemctl --user disable morning-brief.timer   # disable"
echo ""
echo "To change the time: update morning_briefing_time in review_config.json, then re-run this script."
