#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

echo "=== HOEXECSAFE ==="

# Get fresh snapshot JSON directly from the droplet, suppressing SSH noise
SNAPSHOT_JSON="$(ssh "$REMOTE" 'python3 /usr/local/bin/ho_snapshot.py' 2>/dev/null)"

health="$(printf '%s\n' "$SNAPSHOT_JSON" | jq -r '.health.status // "unknown"')"
infra_allow="$(printf '%s\n' "$SNAPSHOT_JSON" | jq -r '.infra.infra_allow_trades // false')"
gate_blocked="$(printf '%s\n' "$SNAPSHOT_JSON" | jq -r '.infra.gate_blocked // false')"
mode="$(printf '%s\n' "$SNAPSHOT_JSON" | jq -r '.executor.effective_mode // "UNKNOWN"')"
live_enabled="$(printf '%s\n' "$SNAPSHOT_JSON" | jq -r '.executor.live_enabled // false')"
plan_live_usd="$(printf '%s\n' "$SNAPSHOT_JSON" | jq -r '.plan.total_live_usd // 0')"
model_budget="$(printf '%s\n' "$SNAPSHOT_JSON" | jq -r '.model.budget_usd // 0')"

echo "health         : $health"
echo "infra_allow    : $infra_allow"
echo "gate_blocked   : $gate_blocked"
echo "mode           : $mode"
echo "live_enabled   : $live_enabled"
echo "plan_live_usd  : $plan_live_usd"
echo "model_budget   : $model_budget"

# Hard safety checks
if [ "$health" != "healthy" ]; then
  echo "[BLOCK] health != healthy -> aborting execution"
  exit 1
fi

if [ "$infra_allow" != "true" ]; then
  echo "[BLOCK] infra_allow_trades != true -> aborting execution"
  exit 1
fi

# Gate check: STRICT ONLY when not in DRYRUN
if [ "$gate_blocked" = "true" ] && [ "$mode" != "DRYRUN" ]; then
  echo "[BLOCK] gate_blocked == true in non-DRYRUN mode -> aborting execution"
  exit 1
fi

echo "[OK] All checks passed. Running hoexec (currently DRYRUN-only)."

# Call executor wrapper directly (avoid alias issues)
if [ -x "$HOME/hands-off/agent/hoexec.sh" ]; then
  "$HOME/hands-off/agent/hoexec.sh"
else
  # fallback: call remote executor directly
  ssh "$REMOTE" "/usr/bin/python3 /usr/local/bin/ho_executor_from_plan.py"
fi

echo "=== END HOEXECSAFE ==="
