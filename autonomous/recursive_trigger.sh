#!/bin/bash
# RECURSIVE MOONSHOT TRIGGER
# This script triggers the moonshot loop and schedules the next cycle

cd /root/hands-off-engine

# Run the moonshot cycle
python3 autonomous/moonshot_loop.py >> /var/log/hands-off/moonshot.log 2>&1

# Check if we should continue (exponential backoff on failures)
LAST_EXIT=$?
if [ $LAST_EXIT -eq 0 ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Cycle successful, scheduling next"
else
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Cycle failed with exit $LAST_EXIT"
fi
