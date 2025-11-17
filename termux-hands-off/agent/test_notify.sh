#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ENV="$HOME/hands-off/state/tg/bots/handsoff.env"
if [ ! -f "$ENV" ]; then
  echo "[err] Missing $ENV"; exit 1
fi
# shellcheck disable=SC1090
. "$ENV"
: "${TOKEN:?Missing TOKEN in env file}"
: "${CHAT_ID:?Missing CHAT_ID in env file}"

MSG="${1:-Test from Termux}"
API="https://api.telegram.org/bot${TOKEN}/sendMessage"
RESP="$(curl -s -X POST "$API" \
  -d "chat_id=${CHAT_ID}" \
  --data-urlencode "text=${MSG}" \
  -d "parse_mode=HTML")"

OK="$(echo "$RESP" | jq -r '.ok // empty')"
if [ "$OK" = "true" ]; then
  echo "[ok] Message sent"
else
  echo "[err] Telegram API response:"
  echo "$RESP"
  exit 1
fi
