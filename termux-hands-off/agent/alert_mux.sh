#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ENVF="$HOME/hands-off/state/alerts.env"; [ -f "$ENVF" ] && . "$ENVF"
QUIET_START="${QUIET_START:-}"; QUIET_END="${QUIET_END:-}"
DEDUP_SECONDS="${DEDUP_SECONDS:-600}"; DEDUP_MAX="${DEDUP_MAX:-200}"

SRC="gen"; SEV="info"; TITLE=""; BODY=""; NOW="$(date +"%Y-%m-%d %H:%M:%S%z")"
while [ $# -gt 0 ]; do
  case "$1" in
    --src) SRC="$2"; shift 2;;
    --sev) SEV="$2"; shift 2;;
    --title) TITLE="$2"; shift 2;;
    --body) BODY="$2"; shift 2;;
    --) shift; break;;
    *) [ -z "${BODY}" ] && BODY="$1" || BODY="$BODY $1"; shift;;
  esac
done
if [ ! -t 0 ]; then S="$(cat -)"; [ -n "$S" ] && BODY="${BODY:+$BODY\n}$S"; fi
[ -n "$BODY" ] || BODY="(no details)"

# Quiet hours
in_range=0
if [ -n "$QUIET_START" ] && [ -n "$QUIET_END" ]; then
  now_m=$(date +%H%M); qs="${QUIET_START//:}"; qe="${QUIET_END//:}"
  if [ "$qs" -le "$qe" ]; then [ "$now_m" -ge "$qs" ] && [ "$now_m" -lt "$qe" ] && in_range=1
  else [ "$now_m" -ge "$qs" ] || [ "$now_m" -lt "$qe" ] && in_range=1; fi
fi
[ -n "$TITLE" ] || TITLE="${SRC^^} ${SEV^^}"
case "$SEV" in crit|critical|red) ICON="🛑";; warn|yellow) ICON="⚠️";; ok|success|green) ICON="✅";; *) ICON="🔔";; esac
MSG="$ICON *$TITLE*$([ $in_range -eq 1 ] && echo ' (quiet)' )
src: \`$SRC\`   sev: \`$SEV\`
time: $NOW

$BODY"

DEDUP_FILE="$HOME/hands-off/state/alert_dedup.log"; touch "$DEDUP_FILE"
HASH="$(printf '%s|%s|%s' "$SRC" "$SEV" "$BODY" | sha256sum | awk '{print $1}')"; NOWS="$(date +%s)"
awk -v now="$NOWS" -v win="$DEDUP_SECONDS" 'NF==2{ if((now-$2) < (win*10)) print }' "$DEDUP_FILE" > "${DEDUP_FILE}.tmp" || true
mv "${DEDUP_FILE}.tmp" "$DEDUP_FILE"
LAST="$(awk -v h="$HASH" '$1==h{print $2}' "$DEDUP_FILE" | tail -n1)"
if [ -n "$LAST" ] && [ $((NOWS-LAST)) -lt "$DEDUP_SECONDS" ]; then echo "[dedup] Skipped duplicate" >&2; exit 0; fi
{ tail -n "$DEDUP_MAX" "$DEDUP_FILE" 2>/dev/null; echo "$HASH $NOWS"; } > "${DEDUP_FILE}.tmp" && mv "${DEDUP_FILE}.tmp" "$DEDUP_FILE"

"$HOME/hands-off/agent/finpush_tg.sh" "$MSG" || { echo "[err] send failed" >&2; exit 1; }
echo "[ok] alert sent: $SRC/$SEV"
