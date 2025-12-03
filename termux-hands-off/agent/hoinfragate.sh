#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"
STATE="/root/hands-off-out/state"

json="$(ssh "$REMOTE" "cat $STATE/infra_gate.json 2>/dev/null" || echo '')"

if [ -z "$json" ]; then
  echo "infra_gate.json missing on remote"
  exit 0
fi

allow="$(printf '%s\n' "$json" | jq -r '.infra_allow_trades // "unknown"' 2>/dev/null || echo "unknown")"
score="$(printf '%s\n' "$json" | jq -r '.infra_score // "unknown"' 2>/dev/null || echo "unknown")"
reason="$(printf '%s\n' "$json" | jq -r '.infra_reason // "unknown"' 2>/dev/null || echo "unknown")"

echo "infra_allow_trades=$allow score=$score"
echo "reason: $reason"
