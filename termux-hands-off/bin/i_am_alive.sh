#!/data/data/com.termux/files/usr/bin/bash
set -e
TG="$HOME/hands-off/state/tg/bots/handsoff.env"
[ -f "$TG" ] && . "$TG" || true

# Telegram ping (optional if env present)
if [ -n "$TOKEN" ] && [ -n "$CHAT_ID" ]; then
  curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    -d chat_id="$CHAT_ID" -d parse_mode=HTML \
    -d text="🟢 <b>Termux</b> booted & cron warming — $(date -u +"%Y-%m-%d %H:%M:%S UTC")" >/dev/null || true
fi

# Clean cron start
pkill crond 2>/dev/null || true
rm -f /data/data/com.termux/files/usr/var/run/crond.pid
mkdir -p "$HOME/.cron-logs"
nohup crond -n -P >> "$HOME/.cron-logs/cron.log" 2>&1 &
sleep 0.5
exit 0
