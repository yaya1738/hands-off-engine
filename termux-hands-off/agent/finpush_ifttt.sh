#!/data/data/com.termux/files/usr/bin/bash
set -e
CONF="$HOME/hands-off/state/auto_sources.env"
mkdir -p "$(dirname "$CONF")"
touch "$CONF"

# load existing
. "$CONF" 2>/dev/null || true

if [ -z "$IFTTT_WEBHOOK" ]; then
  read -p "Paste your IFTTT Webhook URL (https://maker.ifttt.com/trigger/.../json/with/key/...): " IFTTT_WEBHOOK
  # persist (idempotent: replace or append)
  if grep -q '^IFTTT_WEBHOOK=' "$CONF" 2>/dev/null; then
    sed -i 's#^IFTTT_WEBHOOK=.*#IFTTT_WEBHOOK='"$IFTTT_WEBHOOK"'#' "$CONF"
  else
    echo "IFTTT_WEBHOOK=$IFTTT_WEBHOOK" >> "$CONF"
  fi
fi

echo "[ok] IFTTT webhook saved to $CONF"
