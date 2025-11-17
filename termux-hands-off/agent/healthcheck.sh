#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

NOW_UTC="$(date -u +'%Y-%m-%d %H:%M:%S')"
OK=()
BAD=()

note_ok(){ OK+=("$1"); }
note_bad(){ BAD+=("$1"); }

# --- Load notifiers (silent if missing) ---
TG_ENV="$HOME/hands-off/state/tg/bots/handsoff.env"
IFTTT_ENV="$HOME/hands-off/state/auto_sources.env"
[ -f "$TG_ENV" ] && . "$TG_ENV" || true
[ -f "$IFTTT_ENV" ] && . "$IFTTT_ENV" || true

send_tg(){
  local MSG="$1"
  if [ -n "${TOKEN:-}" ] && [ -n "${CHAT_ID:-}" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
      -d "chat_id=${CHAT_ID}" -d "text=${MSG}" >/dev/null || true
  fi
}

send_ifttt(){
  local title="$1" body="$2"
  if [ -n "${IFTTT_WEBHOOK:-}" ]; then
    curl -s -X POST "$IFTTT_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "{\"value1\":\"${title}\",\"value2\":\"${body}\",\"value3\":\"${NOW_UTC} UTC\"}" >/dev/null || true
  fi
}

# --- 1) crond up? ---
if pgrep -f 'crond -n -P' >/dev/null 2>&1; then
  note_ok "crond: running"
else
  note_bad "crond: NOT running"
fi

# --- 2) Key files exist & are fresh ---
DATA_DIR="$HOME/hands-off"
AGENT_DIR="$HOME/hands-off/agent"
LOG_DIR="$HOME/.cron-logs"

# Define expected outputs (adjust if your filenames differ)
PM_COMPACT="$DATA_DIR/polymarket-compact.json"

check_fresh(){
  local f="$1" max_age_min="$2" label="$3"
  if [ ! -f "$f" ]; then
    note_bad "$label: missing ($f)"
    return
  fi
  local age_min=$(( ( $(date +%s) - $(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f") ) / 60 ))
  if [ "$age_min" -le "$max_age_min" ]; then
    note_ok "$label: fresh (${age_min}m)"
  else
    note_bad "$label: STALE (${age_min}m > ${max_age_min}m)"
  fi
}

# 15-min freshness guard for polymarket compact
check_fresh "$PM_COMPACT" 20 "polymarket-compact.json"

# --- 3) Disk space guard ---
# Alert if less than 500MB free on /data
FREE_MB=$(df -Pm /data 2>/dev/null | awk 'NR==2{print $4}')
if [ -n "$FREE_MB" ] && [ "$FREE_MB" -lt 500 ]; then
  note_bad "disk: low space (${FREE_MB} MB free)"
else
  note_ok "disk: ${FREE_MB:-?} MB free"
fi

# --- 4) Recent error lines in cron logs ---
ERRS=$(grep -iE "error|traceback|fail|exception" "$LOG_DIR"/*.log 2>/dev/null | tail -n 5 || true)
if [ -n "$ERRS" ]; then
  note_bad "logs: recent errors detected"
else
  note_ok "logs: clean (no recent errors)"
fi

# --- Build report ---
join_arr(){
  local IFS=$'\n'
  echo "$*"
}

STATUS="✅ HEALTHCHECK ($NOW_UTC)\n"
if [ "${#BAD[@]}" -gt 0 ]; then
  STATUS="❌ HEALTHCHECK ($NOW_UTC)\n"
fi

REPORT="${STATUS}\n"
if [ "${#BAD[@]}" -gt 0 ]; then
  REPORT+="- Issues:\n$(for b in "${BAD[@]}"; do echo "  • $b"; done)\n"
fi
REPORT+="- OK:\n$(for o in "${OK[@]}"; do echo "  • $o"; done)"

# --- Notify on problems; quiet success (except daily rollup) ---
if [ "${#BAD[@]}" -gt 0 ]; then
  send_tg "$REPORT"
  send_ifttt "Hands-Off ALERT" "$REPORT"
fi

# Optional: if called with --always, also send a success ping
if [ "${1:-}" = "--always" ]; then
  send_tg "$REPORT"
fi

# Print to stdout for logs
echo -e "$REPORT"
