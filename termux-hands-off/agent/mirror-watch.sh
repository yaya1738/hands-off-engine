#!/usr/bin/env bash
set -euo pipefail

TRIGGER="$HOME/hands-off/state/mirror.trigger"
SHIP="$HOME/hands-off/agent/mirror_ship.sh"
STATE_DIR="$HOME/hands-off/state"
PIDFILE="$STATE_DIR/mirror-watch.pid"

mkdir -p "$STATE_DIR"

# --- single-instance guard ---
if [ -f "$PIDFILE" ]; then
  old_pid="$(cat "$PIDFILE" || true)"
  if [ -n "${old_pid:-}" ] && kill -0 "$old_pid" 2>/dev/null; then
    # another instance is already running → exit quietly
    exit 0
  fi
fi

echo "$$" > "$PIDFILE"

while true; do
  if [ -f "$TRIGGER" ]; then
    echo "[watcher] trigger detected → running mirror_ship" >&2
    rm -f "$TRIGGER"
    "$SHIP" || echo "[watcher] mirror_ship failed" >&2
  fi
  sleep 1
done
