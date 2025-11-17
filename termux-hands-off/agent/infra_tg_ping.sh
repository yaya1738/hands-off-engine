#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/hands-off"
TG_ENV="$BASE/state/tg/bots/handsoff.env"

# Load TOKEN and CHAT_ID if present
if [ -f "$TG_ENV" ]; then
  # shellcheck disable=SC1090
  . "$TG_ENV"
fi

if [ -z "$TOKEN" ] || [ -z "$CHAT_ID" ]; then
  echo "[warn] TOKEN or CHAT_ID missing in $TG_ENV; skipping infra ping" >&2
  exit 0
fi

INFRA_URL="http://138.68.103.156:8001/txt/infra"
BODY="$(curl -s "$INFRA_URL" || echo "infra endpoint unreachable")"

TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
MSG="🛠 Infra status @ ${TS}\n${BODY}"

curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  --data-urlencode "text=${MSG}" \
  >/dev/null 2>&1 || echo "[warn] Telegram send failed" >&2
