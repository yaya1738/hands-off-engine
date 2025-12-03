#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"
STATE="/root/hands-off-out/state"

# Condition: if any critical state files are missing or corrupted → restore snapshot
ssh "$REMOTE" <<'EOF'
set -e

critical=(
  "$STATE/polymarket-compact.json"
  "$STATE/polymarket-model.json"
  "$STATE/decision_report.json"
  "$STATE/health.json"
  "$STATE/infra.txt"
)

restore_needed=false

for f in "${critical[@]}"; do
    if [[ ! -s "$f" ]]; then
        echo "[warn] missing or empty: $f"
        restore_needed=true
    fi
done

if [[ "$restore_needed" == true ]]; then
    echo "[info] auto-recovery triggered"

    # pick newest snapshot
    SNAPDIR="/root/hands-off-out/snapshots"
    SNAP=$(ls -1t "$SNAPDIR" | head -n 1)

    echo "[info] restoring snapshot: $SNAP"
    tar -xzf "$SNAPDIR/$SNAP" -C /
    echo "[ok] snapshot restored"
else
    echo "[ok] system healthy — no recovery needed"
fi
EOF
