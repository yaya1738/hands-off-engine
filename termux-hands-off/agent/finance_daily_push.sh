#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

FIN_URL="http://138.68.103.156/txt/finance_text"
TG_ENV="$HOME/hands-off/state/tg/bots/handsoff.env"
LOG="$HOME/.cron-logs/finance_daily_push.log"

# load Telegram token & chat id
. "$TG_ENV"

# fetch finance text
TXT="$(curl -sS "$FIN_URL" || echo "[warn] could not fetch $FIN_URL")"

# compose and send
MSG="💰 Daily Finance — $(date -u +'%Y-%m-%d %H:%M UTC')\n$TXT"
curl -sS -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
     -d chat_id="$CHAT_ID" \
     --data-urlencode text="$MSG" \
     > /dev/null

echo "[ok] sent daily finance to Telegram at $(date -u)" >> "$LOG"
