#!/usr/bin/env bash
# horestore.sh - restore /root/hands-off-out on droplet from a snapshot
#
# DANGER:
# - This will MOVE the current /root/hands-off-out to /root/hands-off-out.bak-<TS>
# - Then it will untar a snapshot to recreate /root/hands-off-out
#
# Usage:
#   horestore                 # restore from latest snapshot on droplet
#   horestore hands-off-YYYYMMDDTHHMMSSZ.tar.gz   # restore from specific snapshot

set -euo pipefail

REMOTE="do138"
REMOTE_SNAP_DIR="/root/hands-off-out/snapshots"

SNAP_ARG="${1:-}"

if [[ -n "$SNAP_ARG" ]]; then
  SNAP_BASENAME="$SNAP_ARG"
else
  echo "[info] selecting latest snapshot on $REMOTE..."
  SNAP_PATH="$(ssh "$REMOTE" 'ls -t /root/hands-off-out/snapshots/hands-off-*.tar.gz 2>/dev/null | head -n 1')"
  if [[ -z "$SNAP_PATH" ]]; then
    echo "[error] no snapshots found in $REMOTE_SNAP_DIR on $REMOTE"
    exit 1
  fi
  SNAP_BASENAME="$(basename "$SNAP_PATH")"
fi

echo
echo "======================================================"
echo " RESTORE PLAN (REMOTE: $REMOTE)"
echo "------------------------------------------------------"
echo "  Target directory : /root/hands-off-out"
echo "  Snapshot to use  : $SNAP_BASENAME"
echo "  Snapshot location: $REMOTE_SNAP_DIR/$SNAP_BASENAME"
echo "  Action:"
echo "    1) On droplet, move /root/hands-off-out -> /root/hands-off-out.bak-<timestamp> (if exists)"
echo "    2) Extract snapshot from $REMOTE_SNAP_DIR/$SNAP_BASENAME into /root (recreating hands-off-out)"
echo "======================================================"
echo
read -r -p "Type RESTORE (ALL CAPS) to proceed, or anything else to abort: " CONFIRM

if [[ "$CONFIRM" != "RESTORE" ]]; then
  echo "[info] restore aborted by user."
  exit 0
fi

echo "[info] starting RESTORE on $REMOTE using snapshot: $SNAP_BASENAME"

ssh "$REMOTE" "set -e
  SNAP_FILE=\"/root/hands-off-out/snapshots/$SNAP_BASENAME\"

  echo \"[remote] checking snapshot: \$SNAP_FILE\"
  if [ ! -f \"\$SNAP_FILE\" ]; then
    echo \"[remote][error] snapshot file not found: \$SNAP_FILE\"
    exit 1
  fi

  cd /root

  TS=\$(date -u +%Y%m%dT%H%M%SZ)

  if [ -d hands-off-out ]; then
    BAK_DIR=\"hands-off-out.bak-\$TS\"
    echo \"[remote] moving existing hands-off-out -> \$BAK_DIR\"
    mv hands-off-out \"\$BAK_DIR\"
  else
    echo \"[remote] no existing /root/hands-off-out directory (nothing to move)\"
  fi

  echo \"[remote] extracting snapshot \$SNAP_FILE into /root...\"
  tar xzf \"\$SNAP_FILE\"

  echo \"[remote] restore complete.\"
  echo \"[remote] contents of /root:\"
  ls -ld /root/hands-off-out /root/hands-off-out.bak-* 2>/dev/null || true
"

echo "[ok] restore operation finished (see logs above for details)."
