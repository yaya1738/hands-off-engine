#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
kill "$(cat "$HOME/hands-off/autopilot/loop.pid" 2>/dev/null)" 2>/dev/null || true
kill "$(cat "$HOME/hands-off/control.pid" 2>/dev/null)" 2>/dev/null || true
pkill -f "bash $HOME/hands-off/run_loop.sh" 2>/dev/null || true
pkill -f "python autopilot/control_server.py" 2>/dev/null || true
termux-wake-unlock || true
echo "[OK] stopped"
