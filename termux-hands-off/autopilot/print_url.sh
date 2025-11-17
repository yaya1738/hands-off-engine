#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
URL_FILE="$HOME/hands-off/autopilot/tunnel_url.txt"
if [ -s "$URL_FILE" ]; then
  cat "$URL_FILE"
else
  grep -aEo 'https://[[:alnum:]-]+\.trycloudflare\.com' "$HOME/hands-off/tunnel.log" | tail -n 1
fi
