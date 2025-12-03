#!/usr/bin/env bash
set -euo pipefail

LOG="$HOME/.cron-logs/ho-cycle.log"
STAMP_DIR="$HOME/hands-off/state"

touch "$STAMP_DIR/cycle.touch" || true

{
  echo "===== $(date -Is) ====="
  echo "[cycle] start"

  # 1. Check health
  echo "[cycle] health check"
  hohealth || echo "[warn] health failed"

  # 2. Ensure decision is fresh
  echo "[cycle] run: decider.service"
  ssh do138 "systemctl start decider.service" || echo "[warn] decider error"

  # 3. Rebuild execution plan
  echo "[cycle] run: ho_executor_plan.sh"
  ssh do138 "/usr/local/bin/ho_executor_plan.sh" || echo "[warn] plan rebuild error"

  # 4. Run executor with gate checks
  echo "[cycle] run: hoexecsafe"
  hoexecsafe || echo "[warn] hoexecsafe reported issues"

  echo "[cycle] done"
  echo
} >> "$LOG" 2>&1
