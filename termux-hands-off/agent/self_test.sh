#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

BIN="$HOME/hands-off/bin"
LOG="$HOME/.cron-logs/self_test.log"
mkdir -p "$(dirname "$LOG")"

ts() { date -u +"%Y-%m-%d %H:%M:%S UTC"; }

# Checks
NET="down"
if curl -m 6 -s https://api.telegram.org >/dev/null; then NET="up"; fi

CRON_PIDS="$(pgrep -fa crond || true)"
CRON_STATE="down"
[ -n "$CRON_PIDS" ] && CRON_STATE="up"

DISK="$(df -h . | awk 'NR==2{print $5" used, " $4" free"}')"

# Optional: detect your DO droplet (if you’ve set one)
DO_SSH="${DO_IP:-}"
if [ -f "$HOME/hands-off/state/mirror.env" ]; then
  # shellcheck disable=SC1090
  . "$HOME/hands-off/state/mirror.env" || true
  DO_SSH="${DO_IP:-$DO_SSH}"
fi

OUT="$(cat <<TXT
<b>Hands-Off Heartbeat</b> — $(ts)
• Network: <b>$NET</b>
• Cron: <b>$CRON_STATE</b>
• Disk (Termux): <code>$DISK</code>
• crond: <code>${CRON_PIDS:-none}</code>
• DO target: <code>${DO_SSH:-unset}</code>
TXT
)"

echo "[$(ts)] NET=$NET CRON=$CRON_STATE DISK=($DISK) DO=(${DO_SSH:-unset})" >> "$LOG"
"$BIN/tg.sh" "$OUT"
