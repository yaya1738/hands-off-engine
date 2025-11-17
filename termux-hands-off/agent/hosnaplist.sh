#!/usr/bin/env bash
set -euo pipefail

LOCAL_DIR="$HOME/hands-off/backups"
REMOTE="do138"
REMOTE_SNAP_DIR="/root/hands-off-out/snapshots"

echo "=== LOCAL SNAPSHOTS ($LOCAL_DIR) ==="
ls -lh "$LOCAL_DIR"/hands-off-*.tar.gz 2>/dev/null || echo "  (none)"

echo
echo "=== REMOTE SNAPSHOTS ($REMOTE:$REMOTE_SNAP_DIR) ==="
ssh "$REMOTE" "ls -lh $REMOTE_SNAP_DIR/hands-off-*.tar.gz 2>/dev/null || echo '  (none)'" || echo "  (ssh failed)"
