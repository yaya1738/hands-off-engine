#!/usr/bin/env bash
# hosafepatch: take snapshot, then run a user-specified command safely
set -euo pipefail

SNAP="$HOME/hands-off/agent/hosnapshot.sh"

if [ "$#" -lt 1 ]; then
  echo "Usage: hosafepatch '<command>'"
  exit 1
fi

CMD="$*"

echo "[safe] taking snapshot before running command..."
"$SNAP"   # <-- absolute path, no alias

echo "[safe] running command:"
echo "  $CMD"
eval "$CMD"

echo "[safe] command finished."
