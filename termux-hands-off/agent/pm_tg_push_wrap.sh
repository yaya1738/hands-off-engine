#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
JSON="${COMPACT_JSON:-$HOME/hands-off/out/polymarket-compact.json}"
TG_ENV="$HOME/hands-off/state/tg/bots/handsoff.env"

# Load Telegram creds
. "$TG_ENV" 2>/dev/null || true
TOKEN="${TOKEN:-}"
CHAT_ID="${CHAT_ID:-}"

if [ -f "$JSON" ] && [ -s "$JSON" ] && [ -n "${TOKEN}" ] && [ -n "${CHAT_ID}" ]; then
  PREVIEW="$(jq -r '[
    "📊 Polymarket compact",
    (.meta.timestamp // now | todateiso8601),
    "Top markets:",
    ( .markets[0:5][]? | "- " + (.title//"") + " [" + ((.price*100|round|tostring)+"%") + "]" )
  ] | join("\n")' "$JSON" 2>/dev/null || echo "(compact json present)")"
  curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
       -d chat_id="$CHAT_ID" -d text="$PREVIEW" >/dev/null 2>&1 || true
fi

# Call the original push script
exec /data/data/com.termux/files/usr/bin/python "$HOME/hands-off/agent/pm_tg_push.py"
