#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ENV="$HOME/hands-off/state/tg/bots/handsoff.env"
[ -f "$ENV" ] || { echo "[err] env not found: $ENV" >&2; exit 1; }
# shellcheck disable=SC1090
. "$ENV"

: "${TOKEN:?missing TOKEN in env}"
: "${CHAT_ID:?missing CHAT_ID in env}"

TEXT="${1:-"(no text)"}"
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" \
  --data-urlencode text="$TEXT" \
  -d parse_mode=HTML >/dev/null
