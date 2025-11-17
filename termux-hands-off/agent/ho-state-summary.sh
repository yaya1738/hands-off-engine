#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

# Fetch snapshot JSON from the droplet
SNAP_JSON=$(ssh "$REMOTE" "/usr/bin/python3 /usr/local/bin/ho_snapshot.py")

# Render a compact one-line summary
echo "$SNAP_JSON" | jq -r '
  . as $s |
  # Normalize allow/block flags to strings ("true"/"false")
  ( $s.infra.infra_allow_trades // false | tostring ) as $allowS |
  ( $s.infra.gate_blocked // false | tostring ) as $blockedS |
  "as_of=\($s.as_of // "unknown") " +
  "health=\($s.health.status // "unknown") " +
  "mode=\($s.executor.effective_mode // "unknown") " +
  "tradeable=\(
    if ($allowS == "true") and ($blockedS != "true")
    then "YES" else "NO" end
  ) " +
  "budget=\($s.model.budget_usd // 0) " +
  "events=\($s.model.events // 0) " +
  "plan_live_usd=\($s.plan.total_live_usd // 0) " +
  "finance_total_usd=\($s.finance.total_usd // 0)"
'
