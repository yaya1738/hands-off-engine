#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

echo "[step] running horebuild on droplet (model -> orders -> plan)..."
ssh "$REMOTE" "/usr/local/bin/horebuild.sh"
