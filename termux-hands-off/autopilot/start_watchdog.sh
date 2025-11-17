#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
APD="$HOME/hands-off/autopilot"
if pgrep -f "$APD/watchdog.sh" >/dev/null 2>&1; then
  echo "[OK] watchdog already running"
  exit 0
fi
nohup bash "$APD/watchdog.sh" > "$HOME/hands-off/watchdog.log" 2>&1 &
echo $! > "$APD/watchdog.pid"
echo "[OK] watchdog started"
