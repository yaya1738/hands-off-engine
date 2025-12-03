#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/.cron-logs"
mkdir -p "$LOG_DIR"

EXECUTOR="$HOME/hands-off-out/state/executor_report.json"
DECISION="$HOME/hands-off-out/state/decision_report.json"
TG_SEND="$HOME/hands-off/agent/tg_send.sh"

ts=$(date -Is)

# --- check executor health ---
if [[ -f "$EXECUTOR" ]]; then
    status=$(jq -r '.status' "$EXECUTOR" 2>/dev/null || echo "missing")
    rc=$(jq -r '.return_code' "$EXECUTOR" 2>/dev/null || echo "missing")
else
    status="missing"
    rc="missing"
fi

if [[ "$status" != "ok" ]] || [[ "$rc" != "0" ]]; then
    MSG="⚠️ EXECUTOR ALERT ($ts)
status: $status
return_code: $rc
Check via: hosummary / hoorders"
    "$TG_SEND" "$MSG" || true
fi

# --- detect big edge ---
if [[ -f "$DECISION" ]]; then
    big=$(jq -r '
      .polymarket.model.events[]
      | select(.edge_pct_points >= 10)
      | "\(.id) edge=\(.edge_pct_points)pp (price=\(.price))"
    ' "$DECISION" 2>/dev/null || echo "")

    if [[ -n "$big" ]]; then
        MSG="🔥 BIG EDGE DETECTED ($ts)
$big"
        "$TG_SEND" "$MSG" || true
    fi
fi

echo "[$ts] exec-alerts done" >> "$LOG_DIR/hoexec-alerts.log"
