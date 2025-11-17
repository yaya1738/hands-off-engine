#!/data/data/com.termux/files/usr/bin/bash
set -e
pgrep -f 'crond -n -P' >/dev/null 2>&1 || nohup crond -n -P >> "$HOME/.cron-logs/cron.log" 2>&1 &
