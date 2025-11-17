#!/usr/bin/env bash
set -euo pipefail

LOG="$HOME/.cron-logs/hoexecsafe.log"

{
  echo "===== $(date -Is) ====="
  hoexecsafe
  echo
} >> "$LOG" 2>&1
