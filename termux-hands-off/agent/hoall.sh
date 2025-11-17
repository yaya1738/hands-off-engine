#!/usr/bin/env bash
# hoall - unified Hands-Off overview using direct script paths
set -euo pipefail

AGENT="$HOME/hands-off/agent"

echo "============== HANDS-OFF DASH =============="
"$AGENT/hodash.sh" || echo "[warn] hodash failed"

echo
echo "============== HANDS-OFF ORDERS ============"
"$AGENT/hoorders.sh" || echo "[warn] hoorders failed"

echo
echo "============== POLYMARKET MODEL ============"
"$AGENT/homodel.sh" || echo "[warn] homodel failed"

echo
echo "============== POLYMARKET COMPACT =========="
"$AGENT/homarkets.sh" || echo "[warn] homarkets failed"
