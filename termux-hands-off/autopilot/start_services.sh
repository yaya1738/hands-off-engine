#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
bash "$HOME/hands-off/autopilot/start_admin.sh" || true
BASE="$HOME/hands-off"
LOGD="$BASE"
APD="$BASE/autopilot"
mkdir -p "$APD"

CONTROL_TOKEN="$(cat "$BASE/control.token")"
termux-wake-lock || true

# control server (under venv)
if ! pgrep -f "python autopilot/control_server.py" >/dev/null 2>&1; then
  nohup bash -lc 'cd "$HOME/hands-off"; source .venv/bin/activate; env CONTROL_TOKEN='"$CONTROL_TOKEN"' python autopilot/control_server.py' \
    > "$LOGD/control.log" 2>&1 &
  echo $! > "$APD/control.pid"
fi

# kill any tunnel + clear logs
pkill -f "cloudflared tunnel --url http://localhost:8765" 2>/dev/null || true
rm -f "$LOGD/tunnel.log" "$APD/tunnel_url.txt"

# start new quick tunnel (IPv4, http/2, 2 conns)
nohup cloudflared tunnel --no-autoupdate --loglevel info \
  --logfile "$LOGD/tunnel.log" \
  --edge-ip-version 4 \
  --protocol http2 \
  --ha-connections 2 \
  --url http://localhost:8765 \
  >/dev/null 2>&1 &
echo $! > "$APD/tunnel.pid"

# wait up to ~60s for URL (refresh every 2s)
for i in $(seq 1 30); do
  URL="$(grep -aEo 'https://[[:alnum:]-]+\.trycloudflare\.com' "$LOGD/tunnel.log" | tail -n 1 || true)"
  if [ -n "${URL:-}" ]; then
    echo "$URL" > "$APD/tunnel_url.txt"
    echo "[OK] services started — $URL"
    exit 0
  fi
  sleep 2
done

echo "[WARN] services started but no URL captured; check: tail -n 200 \"$LOGD/tunnel.log\"" >&2
exit 0
