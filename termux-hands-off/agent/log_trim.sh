#!/data/data/com.termux/files/usr/bin/bash
set -e
LOGDIR="$HOME/.cron-logs"
mkdir -p "$LOGDIR"
find "$LOGDIR" -type f -name '*.log' -size +5M -print0 | while IFS= read -r -d '' f; do
  tail -n 2000 "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
done
