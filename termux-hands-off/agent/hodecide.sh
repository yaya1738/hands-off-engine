#!/usr/bin/env bash
# hodecide - run decider to generate DRYRUN orders
set -euo pipefail

REMOTE="do138"

echo "[hodecide] running decider..."
ssh "$REMOTE" "/usr/bin/python3 /root/hands-off-engine/termux-hands-off/agent/pm_decide.py"
echo "[hodecide] done"
