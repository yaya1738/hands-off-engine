#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

BASE="$HOME/hands-off/autopilot"
STATE="$BASE/state.env"
TOKEN="$(cat "$HOME/hands-off/control.token")"
URL_LOCAL="http://127.0.0.1:8765"

# defaults if no state file yet
THR_DEFAULT="${EDGE_THRESHOLD:-0.05}"
THR_MIN="0.02"
STEP="0.01"
QUIET_CYCLES=6   # 6*10min = ~1h at default sleep
SLEEP_SEC=600

# load prior state if exists
if [ -f "$STATE" ]; then
  # shellcheck disable=SC1090
  . "$STATE"
fi
THR="${THR:-$THR_DEFAULT}"
EMPTY_COUNT="${EMPTY_COUNT:-0}"

while true; do
  # pause gate (touch autopilot/PAUSED to pause the loop)
  if [ -f "$BASE/PAUSED" ]; then
    sleep "$SLEEP_SEC"
    continue
  fi
  OUT="$(curl -s -H "X-Token: $TOKEN" "$URL_LOCAL/run/notify_once?v=$THR" || true)"

  if printf '%s' "$OUT" | grep -q '\[BUY'; then
    # had an edge -> reset
    THR="$THR_DEFAULT"
    EMPTY_COUNT=0
  else
    # no edge this cycle
    EMPTY_COUNT=$((EMPTY_COUNT+1))
    if [ "$EMPTY_COUNT" -ge "$QUIET_CYCLES" ]; then
      # lower threshold by one step (floor THR_MIN)
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
  sleep "$SLEEP_SEC"
done
