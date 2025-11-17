#!/data/data/com.termux/files/usr/bin/bash
set -e
MSG="${1:-Heartbeat}"
NOW="$(date -Iseconds)"
termux-notification --title "Hands-Off" --content "$MSG @ $NOW"
echo "[$NOW] $MSG" >>"$HOME/.cron-logs/local.log"
