#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BASE="$HOME/hands-off/autopilot"
URL_FILE="$BASE/tunnel_url.txt"
LOGFILE="$BASE/edges-$(date -u +%Y%m%d).log"
STATE="$BASE/state.env"

echo "=== STATUS @ $(date -u +"%Y-%m-%d %H:%MZ") ==="
printf "watchdog: "; pgrep -f "$BASE/watchdog.sh" >/dev/null && echo "up" || echo "down"
printf "control : "; pgrep -f "python autopilot/control_server.py" >/dev/null && echo "up" || echo "down"
printf "tunnel  : "; pgrep -f "cloudflared tunnel --url http://localhost:8765" >/dev/null && echo "up" || echo "down"
printf "loop    : "; pgrep -f "$BASE/run_loop.sh" >/dev/null && echo "up" || echo "down"
printf "admin  : "; pgrep -f "admin_server.py" >/dev/null && echo "up" || echo "down"

echo -n "url     : "; [ -s "$URL_FILE" ] && cat "$URL_FILE" || echo "NONE"
echo -n "state   : "; [ -s "$STATE" ] && cat "$STATE" | tr '\n' ' ' && echo || echo "NONE"

echo "---- last edges ----"
tail -n 12 "$LOGFILE" 2>/dev/null || echo "(no log yet)"
