#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
LOGFILE="${1:-$HOME/hands-off/autopilot/edges-$(date -u +%Y%m%d).log}"
# Escape quotes for notification payload
MSG="$(tail -n 8 "$LOGFILE" | sed -e 's/"/\\"/g')"
termux-notification --title "EDGE ALERT" --content "$MSG" >/dev/null 2>&1 || true
