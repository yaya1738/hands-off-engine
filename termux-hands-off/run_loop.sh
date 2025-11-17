#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/hands-off/autopilot"
source "$HOME/hands-off/.venv/bin/activate"
while true; do
  echo "--- $(date '+%Y-%m-%d %H:%M:%S') — run" && ./notify_once.sh || echo "Run failed"
  sleep 1800
done
