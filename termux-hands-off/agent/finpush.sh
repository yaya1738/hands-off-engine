#!/data/data/com.termux/files/usr/bin/bash
set -e
CONF="$HOME/hands-off/state/auto_sources.env"
[ -f "$CONF" ] && . "$CONF"

: "${SHEETS_WEBHOOK:?SHEETS_WEBHOOK missing in auto_sources.env}"
: "${SHEETS_TOKEN:?SHEETS_TOKEN missing in auto_sources.env}"
TAB="${SHEETS_TAB:-equity}"

# Build TSV (daily closes)
DATA="$(~/hands-off/agent/finhist.sh all --daily)"
[ -n "$DATA" ] || { echo "[finpush] no data"; exit 0; }

# 1) Resolve *final* URL (follow all redirects) WITHOUT changing method
FINAL="$(curl -sS -o /dev/null -w '%{url_effective}' -L \
  "${SHEETS_WEBHOOK}?token=${SHEETS_TOKEN}&tab=${TAB}")"
[ -n "$FINAL" ] || { echo "[finpush] failed to resolve final URL"; exit 1; }

# 2) POST directly to FINAL (no -L so POST stays POST)
resp="$(printf "%s" "$DATA" | curl -sS --fail -X POST \
  -H 'Content-Type: text/plain' \
  --data-binary @- \
  "$FINAL")"

echo "[finpush] $(date -u +'%FT%TZ') -> $resp"
