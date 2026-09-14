#!/data/data/com.termux/files/usr/bin/bash
# Hands-Off Engine — auto-start on device boot
# Requires Termux:Boot app installed

REPO="$HOME/hands-off-engine"
LOG_DIR="$REPO/state/logs"
mkdir -p "$LOG_DIR"

# Start Node 1
cd "$REPO"
setsid nohup python3 scripts/node1_runtime.py run >> "$LOG_DIR/node1.log" 2>&1 &

# Start Telegram bridge
setsid nohup python3 scripts/telegram_bridge.py >> "$LOG_DIR/telegram_bridge.log" 2>&1 &

# Start Control Room
setsid nohup python3 scripts/yair_control_room.py >> "$LOG_DIR/control_room.log" 2>&1 &

# Start Health Monitor (runs once, cron handles periodic)
setsid nohup python3 scripts/health_monitor.py >> "$LOG_DIR/health_monitor.log" 2>&1 &
