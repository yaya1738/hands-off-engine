#!/data/data/com.termux/files/usr/bin/bash
set -e
CONF="$HOME/hands-off/state/ifttt.env"
mkdir -p "$(dirname "$CONF")"
touch "$CONF"

read -p "Paste your full IFTTT Webhook URL (looks like https://maker.ifttt.com/trigger/hands_off_push/json/with/key/XXXXXXXX): " URL

if grep -q '^IFTTT_WEBHOOK=' "$CONF" 2>/dev/null; then
  sed -i 's#^IFTTT_WEBHOOK=.*#IFTTT_WEBHOOK='"$URL"'#' "$CONF"
else
  echo "IFTTT_WEBHOOK=$URL" >> "$CONF"
fi

echo "[ok] Webhook saved to $CONF"
