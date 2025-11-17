#!/usr/bin/env bash
set -euo pipefail

echo "[preflight] running health, infra, decider dry-run..."

ssh do138 '
  set -e
  echo "[remote] health:"
  jq . /root/hands-off-out/state/health.json || true
  
  echo "[remote] infra:"
  jq . /root/hands-off-out/state/infra.json || true
  
  echo "[remote] decider dry-run:"
  /usr/local/bin/decider.service --dry-run 2>/dev/null || true
'

echo "[preflight] done."
