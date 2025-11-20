#!/usr/bin/env bash
# hoenrich - enrich polymarket-model.json with live prices and edges
set -euo pipefail

REMOTE="do138"

echo "[hoenrich] enriching model with live prices..."
ssh "$REMOTE" "/usr/bin/python3 /root/hands-off-engine/termux-hands-off/agent/pm_enrich_model.py"
echo "[hoenrich] done"
