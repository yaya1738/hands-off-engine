#!/data/data/com.termux/files/usr/bin/bash
# Termux:Boot auto-start — Supervisor manages all services
# Install: place in ~/.termux/boot/ inside Termux (not proot)
set -euo pipefail

REPO="$HOME/hands-off-engine"
LOG_DIR="$REPO/state/logs"
mkdir -p "$LOG_DIR"

# Start the supervisor (it manages node1_runtime + control_room)
if ! pgrep -f "supervisor.py" > /dev/null 2>&1; then
    setsid nohup python3 "$REPO/scripts/supervisor.py" run \
        >> "$LOG_DIR/supervisor_boot.log" 2>&1 &
fi

# Run bus compaction on boot
python3 "$REPO/scripts/bus_compact.py" --max-blocker-age 24 >> "$LOG_DIR/boot.log" 2>&1 || true
