#!/usr/bin/env bash
set -euo pipefail

echo "================ HANDS-OFF COCKPIT ================"
echo "MODE: DRYRUN ONLY — no live trades are submitted yet."
echo "---------------------------------------------------"
echo

echo "===== HOGATE ====="
"$HOME/hands-off/agent/hogate.sh" || echo "[warn] hogate failed"

echo
echo "===== HOTRADE (plan + orders + insight) ====="
"$HOME/hands-off/agent/hotrade.sh" || echo "[warn] hotrade failed"

echo
echo "===== HOSTATUS ====="
"$HOME/hands-off/agent/hostatus.sh" || echo "[warn] hostatus failed"

echo
echo "===== HOFINANCE ====="
if [ -x "$HOME/hands-off/agent/hofinance.sh" ]; then
  "$HOME/hands-off/agent/hofinance.sh" || echo "[warn] hofinance failed"
else
  echo "[info] hofinance helper not found (optional)"
fi

echo
echo "================ END COCKPIT ================="
