#!/bin/bash
#
# Autonomous System Watchdog
#
# Ensures the autonomous system is ALWAYS running.
# Automatically restarts if it crashes.
#
# Usage:
#   ./watchdog.sh start    # Start watchdog
#   ./watchdog.sh stop     # Stop watchdog
#   ./watchdog.sh status   # Check status
#
# Standard: Yair Siegel Master Level Operations - Full Self-Control

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/state/autonomous_pid.txt"
WATCHDOG_PID_FILE="$PROJECT_DIR/state/watchdog_pid.txt"
LOG_FILE="$PROJECT_DIR/logs/unified_autonomous/live.log"
WATCHDOG_LOG="$PROJECT_DIR/logs/unified_autonomous/watchdog.log"

cd "$PROJECT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$WATCHDOG_LOG"
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

start_autonomous() {
    log "Starting autonomous system..."
    nohup python3 -m autonomous.unified_system --budget 500 >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    log "Started with PID $(cat $PID_FILE)"
}

watchdog_loop() {
    log "Watchdog started"

    while true; do
        if ! is_running; then
            log "WARNING: Autonomous system not running! Restarting..."
            start_autonomous
            sleep 5

            if is_running; then
                log "Successfully restarted"
            else
                log "ERROR: Failed to restart!"
            fi
        fi

        # Check every 30 seconds
        sleep 30
    done
}

case "${1:-}" in
    start)
        # Kill existing watchdog if running
        if [ -f "$WATCHDOG_PID_FILE" ]; then
            old_pid=$(cat "$WATCHDOG_PID_FILE")
            kill "$old_pid" 2>/dev/null || true
        fi

        # Start watchdog in background
        nohup "$0" _loop >> "$WATCHDOG_LOG" 2>&1 &
        echo $! > "$WATCHDOG_PID_FILE"

        echo "Watchdog started (PID: $(cat $WATCHDOG_PID_FILE))"
        echo "Autonomous system will be kept running automatically."
        ;;

    _loop)
        watchdog_loop
        ;;

    stop)
        if [ -f "$WATCHDOG_PID_FILE" ]; then
            kill $(cat "$WATCHDOG_PID_FILE") 2>/dev/null || true
            rm -f "$WATCHDOG_PID_FILE"
            echo "Watchdog stopped"
        fi

        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null || true
            rm -f "$PID_FILE"
            echo "Autonomous system stopped"
        fi
        ;;

    status)
        echo "=== Watchdog Status ==="
        if [ -f "$WATCHDOG_PID_FILE" ] && ps -p $(cat "$WATCHDOG_PID_FILE") > /dev/null 2>&1; then
            echo "Watchdog: RUNNING (PID: $(cat $WATCHDOG_PID_FILE))"
        else
            echo "Watchdog: NOT RUNNING"
        fi

        echo ""
        echo "=== Autonomous System Status ==="
        if is_running; then
            echo "System: RUNNING (PID: $(cat $PID_FILE))"
            ps -o pid,etime,cmd -p $(cat "$PID_FILE") 2>/dev/null
        else
            echo "System: NOT RUNNING"
        fi

        echo ""
        echo "=== Recent Log ==="
        tail -5 "$LOG_FILE" 2>/dev/null || echo "No log"
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start
        ;;

    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
