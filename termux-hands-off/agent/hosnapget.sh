#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: hosnapget <snapshot.tar.gz>" >&2
  exit 1
fi

SNAP="$1"
REMOTE="do138"
LOCAL_DIR="$HOME/hands-off/snapshots"

mkdir -p "$LOCAL_DIR"

echo "[info] downloading $SNAP from $REMOTE..."
scp "$REMOTE:/root/hands-off-out/snapshots/$SNAP" "$LOCAL_DIR/"

echo "[ok] downloaded to: $LOCAL_DIR/$SNAP"
