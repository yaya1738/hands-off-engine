#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ok(){ printf "✅ %s\n" "$1"; }
warn(){ printf "⚠️  %s\n" "$1"; }
bad(){ printf "❌ %s\n" "$1"; }

# Paths
ENV="$HOME/hands-off/state/tg/bots/handsoff.env"
NOTIFY="$HOME/hands-off/agent/notify.py"
WATCHER="$HOME/hands-off/agent/finance_watcher.py"
REG="$HOME/hands-off/state/balances.d"
CRONLOG="$HOME/.cron-logs/cron.log"
HLOG="$HOME/.cron-logs/hourly.log"

echo "— Hands-Off verification —"

# Telegram env
[ -f "$ENV" ] && ok "Telegram env present: $ENV" || bad "Missing $ENV"

# Notifier + watcher
[ -x "$NOTIFY" ] && ok "notify.py executable" || bad "notify.py missing/not exec"
[ -x "$WATCHER" ] && ok "finance_watcher.py executable" || bad "finance_watcher.py missing/not exec"

# balances.d contents
CNT=$(ls -1 "$REG"/*.json 2>/dev/null | wc -l | tr -d ' ')
[ "${CNT:-0}" -ge 1 ] && ok "balances.d has $CNT source file(s)" || warn "No balances yet in $REG (use set_balance)"

# crond running
if pgrep -f 'crond -n -P' >/dev/null 2>&1; then
  ok "crond is running"
else
  bad "crond not running"
fi

# cron entry
if crontab -l 2>/dev/null | grep -q 'hourly.sh'; then
  ok "crontab contains hourly task"
else
  bad "hourly task not found in crontab"
fi

# recent logs
[ -f "$CRONLOG" ] && tail -n 5 "$CRONLOG" || true
[ -f "$HLOG" ] && { echo "--- hourly.log (last 5) ---"; tail -n 5 "$HLOG"; } || true

# test a tiny ping (non-fatal)
python "$NOTIFY" "🧪 Verify check: $(date +'%F %T')" >/dev/null 2>&1 && ok "Telegram send OK" || warn "Telegram send test failed"

echo "— done —"
