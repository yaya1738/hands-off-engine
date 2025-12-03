#!/data/data/com.termux/files/usr/bin/bash
set -e
LOG="$HOME/.cron-logs/finance_bot.log"
PG='finance_bot.py'
if pgrep -f "$PG" >/dev/null 2>&1; then
  echo "[ok] finance_bot already running"
  exit 0
fi
nohup /data/data/com.termux/files/usr/bin/python "$HOME/hands-off/agent/finance_bot.py" >> "$LOG" 2>&1 &
echo "[ok] finance_bot started"
