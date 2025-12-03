#!/usr/bin/env bash
set -euo pipefail

LOG="$HOME/.cron-logs/hospreads.log"

{
  echo "===== $(date -Is) ====="
  ssh do138 'ho-spreads.py'
  echo
} >> "$LOG" 2>&1
