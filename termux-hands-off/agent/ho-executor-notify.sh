#!/bin/bash
# Executor Notification Wrapper
# Run this after ho-executor-plan.sh to push notifications

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[ho-executor-notify] Starting notification push..."

# Check if execution plan exists
PLAN_FILE="$REPO_ROOT/executor/execution_plan.json"
if [ ! -f "$PLAN_FILE" ]; then
    echo "[err] No execution plan found at $PLAN_FILE"
    echo "[info] Run ho-executor-plan.sh first to generate plan"
    exit 1
fi

# Run notification script
python3 "$SCRIPT_DIR/notify_execution_plan.py"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[ok] Notification sent successfully"
else
    echo "[err] Notification failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
