#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"
STATE="/root/hands-off-out/state"

ssh "$REMOTE" bash <<'BASH'
set -e
STATE="/root/hands-off-out/state"

echo "================ HOHEALTH (remote health + infra) ================"

echo
echo "[health.json] (first 80 lines)"
if [ -f "$STATE/health.json" ]; then
  sed -n '1,80p' "$STATE/health.json"
else
  echo "no health.json"
fi

echo
echo "[infra.txt] (first 80 lines)"
if [ -f "$STATE/infra.txt" ]; then
  sed -n '1,80p' "$STATE/infra.txt"
else
  echo "no infra.txt"
fi

echo
echo "================ END HOHEALTH ================="
BASH
