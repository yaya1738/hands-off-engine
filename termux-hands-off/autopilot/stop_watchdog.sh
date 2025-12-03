#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
APD="$HOME/hands-off/autopilot"
pkill -f "$APD/watchdog.sh" 2>/dev/null || true
kill $(cat "$APD/watchdog.pid" 2>/dev/null) 2>/dev/null || true
rm -f "$APD/watchdog.pid" "$APD/watchdog.lock"
echo "[OK] watchdog stopped"
