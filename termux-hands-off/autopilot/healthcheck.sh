#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BASE="$HOME/hands-off"
APD="$BASE/autopilot"
TOKEN="$(cat "$BASE/control.token")"

# 4a) ensure control server responds locally
if ! curl -fsS -m 3 -H "X-Token: $TOKEN" http://127.0.0.1:8765/ping >/dev/null; then
  echo "[HC] control down — restarting"
  bash "$APD/start_services.sh"
fi

# 4b) ensure tunnel is up; refresh URL file
if ! pgrep -f "cloudflared tunnel --url http://localhost:8765" >/dev/null 2>&1; then
  echo "[HC] tunnel down — restarting"
  bash "$APD/start_services.sh"
fi

# update URL file if missing
grep -aEo 'https://[[:alnum:]-]+\.trycloudflare\.com' "$BASE/tunnel.log" | tail -n 1 > "$APD/tunnel_url.txt" || true

# 4c) ping public URL; if it fails, restart tunnel
URL="$(cat "$APD/tunnel_url.txt" 2>/dev/null || true)"
if [ -n "$URL" ]; then
  if ! curl -fsS -m 5 -H "X-Token: $TOKEN" "$URL/ping" >/dev/null; then
    echo "[HC] public URL failed — restarting tunnel"
    pkill -f "cloudflared tunnel --url http://localhost:8765" 2>/dev/null || true
    nohup cloudflared tunnel --url http://localhost:8765 > "$BASE/tunnel.log" 2>&1 &
    echo $! > "$APD/tunnel.pid"
    sleep 2
    grep -aEo 'https://[[:alnum:]-]+\.trycloudflare\.com' "$BASE/tunnel.log" | tail -n 1 > "$APD/tunnel_url.txt" || true
  fi
fi

# refresh URL if a newer one appears in the log

NEW_URL=$(grep -aEo "https://[[:alnum:]-]+\.trycloudflare\.com" "$BASE/tunnel.log" | tail -n 1 || true)

[ -n "$NEW_URL" ] && echo "$NEW_URL" > "$APD/tunnel_url.txt"

echo "[HC] ok"
