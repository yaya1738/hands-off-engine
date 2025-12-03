#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/hands-off"
termux-wake-lock || true
source .venv/bin/activate

# 1) Loop (every 30 mins)
pkill -f "bash $HOME/hands-off/run_loop.sh" 2>/dev/null || true
nohup "$HOME/hands-off/run_loop.sh" > "$HOME/hands-off/autopilot/loop.out" 2>&1 &
echo $! > "$HOME/hands-off/autopilot/loop.pid"

# 2) Control server
pkill -f "python autopilot/control_server.py" 2>/dev/null || true
nohup bash -lc 'cd "$HOME/hands-off"; source .venv/bin/activate; python autopilot/control_server.py' \
  > "$HOME/hands-off/control.log" 2>&1 &
echo $! > "$HOME/hands-off/control.pid"

echo "[OK] loop pid=$(cat "$HOME/hands-off/autopilot/loop.pid"), control pid=$(cat "$HOME/hands-off/control.pid")"
