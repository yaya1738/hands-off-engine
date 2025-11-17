#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
LOG="$HOME/hands-off/tunnel.log"
PIDF="$HOME/hands-off/tunnel.pid"
URLF="$HOME/hands-off/tunnel_url.txt"

# stop old
kill "$(cat "$PIDF" 2>/dev/null)" 2>/dev/null || true
pkill -f 'cloudflared tunnel --url' 2>/dev/null || true

# start new (bind to 127.0.0.1)
nohup cloudflared tunnel --url http://127.0.0.1:8765 \
  > "$LOG" 2>&1 & echo $! > "$PIDF"

# wait and persist URL
sleep 3
URL="$(grep -aEo 'https://[[:alnum:]-]+\.trycloudflare\.com' "$LOG" | tail -n 1)"
[ -n "${URL:-}" ] || { echo "ERR: no URL found" >&2; exit 1; }
printf "%s\n" "$URL" > "$URLF"
echo "Tunnel: $URL"
