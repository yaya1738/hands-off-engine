#!/data/data/com.termux/files/usr/bin/bash
set -e

STATE="/data/data/com.termux/files/home/hands-off/state"
CONF_MAIN="$STATE/ifttt.env"
CONF_ALT="$STATE/auto_sources.env"

USED_CONF=""
if [ -f "$CONF_MAIN" ]; then
  . "$CONF_MAIN"
  USED_CONF="$CONF_MAIN"
elif [ -f "$CONF_ALT" ]; then
  . "$CONF_ALT"
  USED_CONF="$CONF_ALT"
fi

if [ -z "$IFTTT_WEBHOOK" ]; then
  echo "[err] IFTTT_WEBHOOK missing (checked $CONF_MAIN and $CONF_ALT)" >&2
  exit 1
fi

# Optional: try to include a compact Polymarket summary if present
# Known locations (auto-detect first that exists)
CANDIDATES=(
  "/data/data/com.termux/files/home/hands-off/state/polymarket-compact.json"
  "/data/data/com.termux/files/home/hands-off/agent/polymarket-compact.json"
)
PM_COMPACT=""
for f in "${CANDIDATES[@]}"; do
  [ -s "$f" ] && PM_COMPACT="$f" && break
done

TS="$(date -u +'%Y-%m-%d %H:%M:%S UTC')"
HOST="$(uname -n 2>/dev/null || echo termux)"

if [ -n "$PM_COMPACT" ]; then
  # Pull 1-2 concise fields if available; fall back gracefully
  TITLE="$(jq -r '.title // .summary // "Polymarket summary"' "$PM_COMPACT" 2>/dev/null || echo "Polymarket summary")"
  EV="$(jq -r '.ev // .net_ev // empty' "$PM_COMPACT" 2>/dev/null || true)"
  V1="$TITLE"
  V2="${EV:+EV=$EV} ${TS}"
  V3="host=$HOST src=$(basename "$PM_COMPACT")"
else
  V1="Hands-Off heartbeat"
  V2="$TS"
  V3="host=$HOST"
fi

curl -sS -X POST "$IFTTT_WEBHOOK" -H 'Content-Type: application/json' \
  -d "{\"value1\":\"${V1}\",\"value2\":\"${V2}\",\"value3\":\"${V3}\"}" >/dev/null

echo "[info] using conf: ${USED_CONF:-unknown}" 1>&2
echo "[ok] IFTTT push sent @ $TS"
