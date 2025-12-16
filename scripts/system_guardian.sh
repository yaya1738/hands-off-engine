#!/bin/bash
# System Guardian - Protect ALL critical processes from corruption/shutdown
# Ensures hands-off-engine runs 24/7 without interruption

PROTECTION_DIR="/root/hands-off-protection"
PID_DIR="/root/hands-off-engine/state"
LOG_DIR="/var/log/hands-off"

mkdir -p "$PROTECTION_DIR" "$LOG_DIR"

# CRITICAL PROCESSES - These must NEVER stop
declare -A CRITICAL_PROCESSES=(
    ["backend_loop"]="python3 /root/hands-off-engine/autonomous/backend_loop.py"
    ["bounty_monitor"]="python3 /root/hands-off-engine/autonomous/bounty_monitor.py --continuous"
    ["pr_email_bridge"]="python3 /root/hands-off-engine/autonomous/pr_email_bridge.py --continuous"
    ["email_inbox_handler"]="python3 /root/hands-off-engine/autonomous/email_inbox_handler.py --continuous"
    ["money_printer"]="python3 /root/hands-off-engine/MONEY_PRINTER.py"
)

# Protection mechanism: Restart any stopped critical process
protect_process() {
    local name="$1"
    local cmd="$2"

    if ! pgrep -f "$name.py" > /dev/null; then
        echo "[$(date -Iseconds)] PROTECTION: Restarting $name" | tee -a "$LOG_DIR/guardian.log"

        # Start with proper logging
        nohup $cmd >> "$LOG_DIR/${name}.log" 2>&1 &

        sleep 2

        if pgrep -f "$name.py" > /dev/null; then
            PID=$(pgrep -f "$name.py" | head -1)
            echo "[$(date -Iseconds)] ✓ $name restarted (PID $PID)" | tee -a "$LOG_DIR/guardian.log"
        else
            echo "[$(date -Iseconds)] ✗ FAILED to restart $name" | tee -a "$LOG_DIR/guardian.log"
        fi
    fi
}

# Main protection loop
while true; do
    for name in "${!CRITICAL_PROCESSES[@]}"; do
        protect_process "$name" "${CRITICAL_PROCESSES[$name]}"
    done

    # Check every 60 seconds
    sleep 60
done
