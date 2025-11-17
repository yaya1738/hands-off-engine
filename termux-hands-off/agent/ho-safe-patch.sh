#!/usr/bin/env bash
# ho-safe-patch: snapshot => run command => health-check => notify

set -euo pipefail

CMD="${1:-}"

if [[ -z "$CMD" ]]; then
  echo "Usage: ho-safe-patch '<command>'"
  exit 1
fi

echo "[safe] taking snapshot before change..."
hosnapshot

echo "[safe] running user command: $CMD"
eval "$CMD"

echo "[safe] running post-change health checks..."
ssh do138 '/usr/local/bin/ho-health2.sh' || true
ssh do138 '/usr/local/bin/ho-infra2.sh'  || true

echo "[safe] retrieving health status..."
STATUS=$(ssh do138 'jq -r .status /root/hands-off-out/state/health.json')
if [[ "$STATUS" != "healthy" ]]; then
  echo "[ALERT] Post-change health check FAILED — manual attention recommended."
else
  echo "[safe] All systems healthy after change."
fi
