#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BASE="$HOME/hands-off/autopilot"
ENV="$BASE/telegram.env"
read -rp "Paste TELEGRAM_BOT_TOKEN (from @BotFather): " TOK
read -rp "Paste TELEGRAM_CHAT_ID (number): " CID
mkdir -p "$BASE"
printf "TELEGRAM_BOT_TOKEN=%s\nTELEGRAM_CHAT_ID=%s\n" "$TOK" "$CID" > "$ENV"
chmod 600 "$ENV"
# fire a test
. "$ENV"
MSG="edge autopilot ok $(date -u +'%H:%MZ')"
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=$MSG" \
  -d "disable_web_page_preview=true" >/dev/null && echo "[ok] telegram delivered"
