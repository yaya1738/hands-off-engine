#!/data/data/com.termux/files/usr/bin/bash
# Termux:Boot auto-start — Node 1 + Control Room + Telegram bridge
# Install: place in ~/.termux/boot/ inside Termux (not proot)
# Requires: termux-api package for boot events
set -euo pipefail

REPO="$HOME/hands-off-engine"
LOG_DIR="$REPO/state/logs"
mkdir -p "$LOG_DIR"

# Start node1 runtime if not running
if ! pgrep -f "node1_runtime.py" > /dev/null 2>&1; then
    setsid nohup python3 "$REPO/scripts/node1_runtime.py" run \
        >> "$LOG_DIR/node1_boot.log" 2>&1 &
fi

# Start Control Room daemon if not running
if ! pgrep -f "yair_control_room.py" > /dev/null 2>&1; then
    setsid nohup python3 "$REPO/scripts/yair_control_room.py" \
        >> "$LOG_DIR/control_room.log" 2>&1 &
fi

# Run bus compaction on boot (drop stale blockers, dedup)
python3 "$REPO/scripts/bus_compact.py" --max-blocker-age 24 >> "$LOG_DIR/boot.log" 2>&1 || true
