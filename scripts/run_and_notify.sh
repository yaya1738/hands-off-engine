#!/bin/bash
# Hands-Off Engine: Complete Pipeline with Notifications
#
# This script runs the full trading pipeline and sends notifications:
# 1. Sync Polymarket data → Alpha signals
# 2. Decider plans actions
# 3. Executor validates (DRYRUN)
# 4. Notifications sent to Telegram/IFTTT
#
# Designed to be run via cron for automated trading signals.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "[$(date)] Starting Hands-Off Engine pipeline..."

# Run the full pipeline
python3 scripts/run_pipeline.py "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "[ERROR] Pipeline failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi

# Check if execution plan was generated
if [ ! -f "executor/execution_plan.json" ]; then
    echo "[INFO] No execution plan generated (no actions passed safety checks)"
    exit 0
fi

# Send notification
echo "[$(date)] Sending notification..."
python3 termux-hands-off/agent/notify_execution_plan.py
NOTIFY_EXIT=$?

if [ $NOTIFY_EXIT -eq 0 ]; then
    echo "[$(date)] ✓ Pipeline completed and notification sent"
else
    echo "[$(date)] ✗ Pipeline completed but notification failed (exit code $NOTIFY_EXIT)"
    exit $NOTIFY_EXIT
fi

exit 0
