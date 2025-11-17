#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BASE="$HOME/hands-off/autopilot"
ENV="$BASE/telegram.env"
LOGFILE="${1:-$BASE/edges-$(date -u +%Y%m%d).log}"

# shell-style key=val file with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
[ -f "$ENV" ] || { echo "[telegram] $ENV missing"; exit 0; }
# shellcheck disable=SC1090
. "$ENV"

[ -n "${TELEGRAM_BOT_TOKEN:-}" ] || exit 0
[ -n "${TELEGRAM_CHAT_ID:-}" ] || exit 0

MSG="$(tail -n 8 "$LOGFILE" | sed -e 's/[\"\\]/\\&/g')"
API="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"
curl -s -X POST "$API" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=$MSG" \
  -d "disable_web_page_preview=true" \
  -d "parse_mode=MarkdownV2" >/dev/null 2>&1 || true
