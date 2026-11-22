#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PRIVATE_ROOT="${HANDS_OFF_PRIVATE_DIR:-$HOME/.config/hands-off-engine}"
LOG="$PRIVATE_ROOT/logs/hourly.log"
mkdir -p "$(dirname "$LOG")"
chmod 700 "$PRIVATE_ROOT" "$(dirname "$LOG")"
touch "$LOG"
chmod 600 "$LOG"
PY_NOTIFY="$HOME/hands-off/agent/notify.py"

run() { echo "[$(date -Is)] $*"; eval "$@"; }

# --- Your jobs go here (add/remove as you wish) ---

# 1) placeholder: finance watcher if present
if [ -f "$HOME/hands-off/agent/finance_watcher.py" ]; then
  run "python '$HOME/hands-off/agent/finance_watcher.py'"
else
  echo "finance_watcher.py not found — skipping"
fi

# 2) heartbeat (so you know cron ran)
python "$PY_NOTIFY" "⏱️ Hourly heartbeat OK: $(date +'%Y-%m-%d %H:%M:%S')"

