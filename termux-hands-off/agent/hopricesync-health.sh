#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

# First check infra/health
ssh "$REMOTE" "grep -q 'status=healthy' /root/hands-off-out/state/health.json" \
  || { echo '[skip] unhealthy infra → skipping hopricesync'; exit 0; }

# If healthy → run the full sync
$HOME/hands-off/agent/hopricesync.sh
