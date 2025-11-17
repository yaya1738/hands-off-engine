#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"
STATE="/root/hands-off-out/state"
LOGS="/root/hands-off-out/logs"

# 1) Infra gate summary
json="$(ssh "$REMOTE" "cat $STATE/infra_gate.json 2>/dev/null" || echo '')"
if [ -z "$json" ]; then
  echo "[infra] infra_gate.json missing"
else
  allow="$(printf '%s\n' "$json" | jq -r '.infra_allow_trades // "unknown"' 2>/dev/null || echo "unknown")"
  score="$(printf '%s\n' "$json" | jq -r '.infra_score // "unknown"' 2>/dev/null || echo "unknown")"
  reason="$(printf '%s\n' "$json" | jq -r '.infra_reason // "unknown"' 2>/dev/null || echo "unknown")"
  echo "[infra] allow=$allow score=$score"
  echo "[infra] reason: $reason"
fi

echo

# 2) Last executor log line (summary)
last="$(ssh "$REMOTE" "tail -n 1 $LOGS/executor.log 2>/dev/null" || echo '')"
if [ -z "$last" ]; then
  echo "[exec] no executor.log yet"
else
  echo "[exec] last: $last"
fi
