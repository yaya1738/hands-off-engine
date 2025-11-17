#!/usr/bin/env bash
set -euo pipefail

echo "===== AUTOPUSH $(date -Is) ====="

cd "$HOME/hands-off"

git add -A
git commit -m "auto: $(date -Is)" || {
  echo "[skip] nothing to commit."
  exit 0
}

git push origin main
echo "[ok] pushed."
