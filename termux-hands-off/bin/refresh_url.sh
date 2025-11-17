#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
LOG="$HOME/hands-off/tunnel.log"
URLF="$HOME/hands-off/tunnel_url.txt"
URL="$(grep -aEo 'https://[[:alnum:]-]+\.trycloudflare\.com' "$LOG" | tail -n 1)"
[ -n "${URL:-}" ] || { echo "ERR: no URL found" >&2; exit 1; }
printf "%s\n" "$URL" > "$URLF"
echo "Refreshed: $URL"
