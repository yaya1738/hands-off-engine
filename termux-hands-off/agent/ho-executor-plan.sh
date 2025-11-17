#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

ssh "$REMOTE" "sed -n '1,160p' /root/hands-off-out/state/execution_plan.json 2>/dev/null || echo 'no execution_plan.json'"
