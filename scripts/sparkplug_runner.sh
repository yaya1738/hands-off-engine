#!/bin/bash
#
# Spark Plug AI-Runner Cron Wrapper
#
# Runs the AI-Runner to process Spark Plug tasks (memory kernel refreshes)
# Creates a fresh task file each run if none exists.
#
# Usage: ./scripts/sparkplug_runner.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TASKS_DIR="$REPO_ROOT/ai/tasks"
LOG_DIR="/var/log/hands-off"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

cd "$REPO_ROOT"

# Generate task file for this run if no tasks pending
TASK_COUNT=$(ls -1 "$TASKS_DIR"/*.json 2>/dev/null | wc -l || echo "0")

if [ "$TASK_COUNT" -eq 0 ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    TASK_FILE="$TASKS_DIR/sparkplug_auto_${TIMESTAMP}.json"

    cat > "$TASK_FILE" << EOF
{
  "task_type": "sparkplug_autokernel_refresh",
  "task_id": "sparkplug_auto_${TIMESTAMP}",
  "mode": "config",
  "dry_run": false
}
EOF
    echo "[$(date -Iseconds)] Created task file: $TASK_FILE"
fi

# Run AI-Runner
echo "[$(date -Iseconds)] Running AI-Runner process-all..."
python3 "$REPO_ROOT/ai_runner.py" process-all --continue-on-error 2>&1

echo "[$(date -Iseconds)] Spark Plug runner completed"
