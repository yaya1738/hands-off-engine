#!/usr/bin/env bash
# hosnapprune [N]  -> keep N newest local snapshots, delete older ones
set -euo pipefail

KEEP="${1:-7}"
LOCAL_DIR="$HOME/hands-off/backups"

echo "[prune] keeping $KEEP newest snapshots in $LOCAL_DIR"

SNAPS=( $(ls -1t "$LOCAL_DIR"/hands-off-*.tar.gz 2>/dev/null || true) )

COUNT="${#SNAPS[@]}"

if [ "$COUNT" -le "$KEEP" ]; then
  echo "[prune] only $COUNT snapshot(s) found, nothing to delete."
  exit 0
fi

TO_DELETE=( "${SNAPS[@]:$KEEP}" )

echo "[prune] will delete ${#TO_DELETE[@]} older snapshot(s):"
for f in "${TO_DELETE[@]}"; do
  echo "  $f"
done

read -r -p "Type DELETE (ALL CAPS) to remove these files, or anything else to abort: " CONFIRM
if [ "$CONFIRM" != "DELETE" ]; then
  echo "[prune] aborted."
  exit 0
fi

for f in "${TO_DELETE[@]}"; do
  rm -f -- "$f"
done

echo "[prune] done."
