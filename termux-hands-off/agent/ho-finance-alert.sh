#!/usr/bin/env bash
set -euo pipefail

LOG="$HOME/.cron-logs/ho-finance-alert.log"
mkdir -p "$(dirname "$LOG")"

{
  echo "===== $(date -Is) ====="
  "$HOME/hands-off/agent/ho-finance-alert.py"
  echo
} >> "$LOG" 2>&1
