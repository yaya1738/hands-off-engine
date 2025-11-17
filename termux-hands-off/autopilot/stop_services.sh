#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
APD="$HOME/hands-off/autopilot"
kill $(cat "$APD/control.pid" 2>/dev/null) 2>/dev/null || true
kill $(cat "$APD/tunnel.pid" 2>/dev/null) 2>/dev/null || true
pkill -f "python autopilot/control_server.py" 2>/dev/null || true
pkill -f "cloudflared tunnel --url http://localhost:8765" 2>/dev/null || true
termux-wake-unlock || true
echo "[OK] services stopped"
