#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

# Rebuild the plan, then show it
ssh "$REMOTE" "/usr/local/bin/ho_executor_plan.sh >/dev/null 2>&1 || true; sed -n '1,160p' /root/hands-off-out/state/execution_plan.json"
