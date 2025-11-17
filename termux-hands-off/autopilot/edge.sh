#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
T="${1:-0.03}"
URL_FILE="$HOME/hands-off/autopilot/tunnel_url.txt"
TOKEN="$(cat "$HOME/hands-off/control.token")"

echo "[local] threshold=$T"
curl -s -H "X-Token: $TOKEN" "http://127.0.0.1:8765/run/notify_once?v=$T"

if [ -s "$URL_FILE" ]; then
  URL="$(cat "$URL_FILE")"
  echo
  echo "[remote] $URL threshold=$T"
  curl -s -H "X-Token: $TOKEN" "$URL/run/notify_once?v=$T"
fi
