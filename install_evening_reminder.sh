#!/usr/bin/env bash
# Installs a systemd user timer for the evening review reminder.
# Re-run after changing evening_reminder_time in Settings.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
CONFIG_JSON="$SCRIPT_DIR/review_config.json"

# Read time from config, default 21:00
if command -v python3 &>/dev/null && [ -f "$CONFIG_JSON" ]; then
    REMINDER_TIME=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_JSON') as f:
        cfg = json.load(f)
    print(cfg.get('evening_reminder_time', '21:00'))
except Exception:
    print('21:00')
" 2>/dev/null || echo "21:00")
else
    REMINDER_TIME="21:00"
fi

HOUR="${REMINDER_TIME%%:*}"
MINUTE="${REMINDER_TIME##*:}"

UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/evening-reminder.service" <<EOF
[Unit]
Description=Evening Review Reminder

[Service]
Type=oneshot
ExecStart=$VENV_PYTHON $SCRIPT_DIR/evening_reminder.py
EOF

cat > "$UNIT_DIR/evening-reminder.timer" <<EOF
[Unit]
Description=Evening Review Reminder Timer
Requires=evening-reminder.service

[Timer]
OnCalendar=*-*-* ${HOUR}:${MINUTE}:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now evening-reminder.timer

echo "Evening reminder timer installed for ${REMINDER_TIME}."
echo "Run 'systemctl --user status evening-reminder.timer' to verify."
