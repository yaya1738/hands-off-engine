#!/usr/bin/env bash
set -euo pipefail

STATE_CMD="$HOME/hands-off/agent/ho-state-summary.sh"
COCKPIT_CMD="$HOME/hands-off/agent/hocockpit.sh"
SNAPSHOT_CMD="$HOME/hands-off/agent/hosnapshot.sh"

echo "================ HO (Master Quick Panel) ================"

# 1) HOSTATE (one-line summary)
echo
echo "--- HOSTATE ---"
LINE="$("$STATE_CMD" 2>/dev/null || true)"
echo "$LINE"

# 2) Parse health + tradeable from the line
HEALTH=$(printf '%s\n' "$LINE" | awk '{for(i=1;i<=NF;i++) if($i~/^health=/){sub("health=","",$i); print $i}}')
TRADE=$(printf '%s\n' "$LINE" | awk '{for(i=1;i<=NF;i++) if($i~/^tradeable=/){sub("tradeable=","",$i); print $i}}')

echo
echo "--- WARNINGS ---"
if [ -z "$HEALTH" ]; then
  echo "[WARN] Health unknown"
elif [ "$HEALTH" != "healthy" ]; then
  echo "[WARN] Health = $HEALTH"
else
  echo "[ok] Health = healthy"
fi

if [ -z "$TRADE" ]; then
  echo "[WARN] Tradeable unknown"
elif [ "$TRADE" != "YES" ]; then
  echo "[WARN] Tradeable = $TRADE"
else
  echo "[ok] Tradeable = YES"
fi

# 3) Cockpit (trimmed)
echo
echo "--- COCKPIT (trimmed) ---"
"$COCKPIT_CMD" 2>/dev/null | sed -n '1,50p' || echo "[warn] hocockpit failed"

# 4) Snapshot
echo
echo "--- SNAPSHOT ---"
"$SNAPSHOT_CMD" 2>/dev/null || echo "[warn] hosnapshot failed"

echo "================ END HO ================="
