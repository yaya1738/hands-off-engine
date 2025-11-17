#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

echo "================ HOMODELDEMO (RESET DEMO MODEL + REFRESH) ================"
echo "[step] 1/2: reset polymarket-model.json to demo template on droplet..."
ssh "$REMOTE" "/usr/local/bin/ho_model_demo.py"

echo
echo "[step] 2/2: running horefresh (model -> orders -> plan + cockpit)..."
"$HOME/hands-off/agent/horefresh.sh"

echo "================ END HOMODELDEMO ================="
