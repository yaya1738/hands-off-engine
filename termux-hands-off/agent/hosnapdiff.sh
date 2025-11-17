#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: hosnapdiff <snapshot-base>" >&2
  echo "  e.g. hosnapdiff ho-20251116-074045" >&2
  exit 1
fi

SNAP="$1"
REMOTE="do138"

ssh "$REMOTE" "/usr/local/bin/ho_snapdiff.py \"$SNAP\""
