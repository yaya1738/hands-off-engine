#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

ssh "$REMOTE" '
  SNAPDIR="/root/hands-off-out/snapshots"
  if [ ! -d "$SNAPDIR" ]; then
    echo "[warn] snapshot dir does not exist: $SNAPDIR"
    exit 0
  fi

  echo "=== REMOTE SNAPSHOTS ($SNAPDIR) ==="
  ls -lh "$SNAPDIR" | sed "1d" || echo "[info] no snapshots yet"
'
