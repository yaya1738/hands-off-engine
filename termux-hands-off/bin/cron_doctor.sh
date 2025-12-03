#!/data/data/com.termux/files/usr/bin/bash
set -e
LOG="$HOME/.cron-logs/cron_doctor.log"
TS="$(date -u +'%Y-%m-%d %H:%M:%S UTC')"

# Ensure single crond with Termux flags
pkill crond 2>/dev/null || true
rm -f /data/data/com.termux/files/usr/var/run/crond.pid
nohup crond -n -P >> "$HOME/.cron-logs/cron.log" 2>&1 &
sleep 0.3

# De-dup crontab, keep one SHELL and PATH
TMP="$(mktemp)"
crontab -l 2>/dev/null > "$TMP" || true
awk '
BEGIN{seen_shell=0; seen_path=0}
{
  if($0 ~ /^SHELL=/){ if(!seen_shell){ print; seen_shell=1 }; next }
  if($0 ~ /^PATH=/){  if(!seen_path){  print; seen_path=1 };  next }
  if(!seen[$0]++){ print }
}' "$TMP" | crontab -
rm -f "$TMP"

echo "[$TS] cron doctor ran" >> "$LOG"
