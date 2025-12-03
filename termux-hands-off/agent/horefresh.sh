#!/usr/bin/env bash
set -euo pipefail

echo "================ HOFRESH (REBUILD + COCKPIT) ================"
echo "[step] 1/2: horebuild (model -> orders -> plan)..."
"$HOME/hands-off/agent/horebuild.sh" || {
  echo "[error] horebuild failed — aborting before cockpit"
  exit 1
}

echo
echo "[step] 2/2: hocockpit (gate + plan + orders + insight + finance)..."
"$HOME/hands-off/agent/hocockpit.sh" || {
  echo "[warn] hocockpit failed after successful rebuild"
  exit 1
}

echo "================ END HOFRESH ================="
