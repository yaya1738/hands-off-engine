#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BASE="$HOME/hands-off/autopilot"
STATE="$BASE/state.env"
TOKEN="$(cat "$HOME/hands-off/control.token")"
URL_LOCAL="http://127.0.0.1:8765"

THR_DEFAULT="${EDGE_THRESHOLD:-0.05}"
THR_MIN="0.02"
STEP="0.01"
QUIET_CYCLES=6

# load state
[ -f "$STATE" ] && . "$STATE"
THR="${THR:-$THR_DEFAULT}"
EMPTY_COUNT="${EMPTY_COUNT:-0}"

OUT="$(curl -s -H "X-Token: $TOKEN" "$URL_LOCAL/run/notify_once?v=$THR" || true)"
if printf '%s' "$OUT" | grep -q '\[BUY'; then
  THR="$THR_DEFAULT"; EMPTY_COUNT=0
else
  EMPTY_COUNT=$((EMPTY_COUNT+1))
  if [ "$EMPTY_COUNT" -ge "$QUIET_CYCLES" ]; then
    THR="$(python - <<PY
thr=float("$THR"); step=float("$STEP"); thr_min=float("$THR_MIN")
thr=max(thr-step, thr_min)
print(f"{thr:.3f}")
PY
)"
    EMPTY_COUNT=0
  fi
fi
printf 'THR=%s\nEMPTY_COUNT=%s\n' "$THR" "$EMPTY_COUNT" > "$STATE"
echo "[OUT]"
echo "$OUT" | sed -n '1,40p'
echo "[STATE]"
cat "$STATE"
