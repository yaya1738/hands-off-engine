#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
bash "$HOME/hands-off/autopilot/cleanup_logs.sh" >/dev/null 2>&1 || true
APD="$HOME/hands-off/autopilot"
mkdir -p "$APD"
# prevent duplicates via flock
exec 9>"$APD/watchdog.lock"
flock -n 9 || { echo "[watchdog] already running"; exit 0; }
echo $$ > "$APD/watchdog.pid"

while true; do
  bash "$APD/healthcheck.sh" || true
  sleep 120
done
