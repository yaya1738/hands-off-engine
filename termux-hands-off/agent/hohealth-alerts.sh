#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/.cron-logs"
mkdir -p "$LOG_DIR"

TS="$(date -Is)"
TG_SEND="$HOME/hands-off/agent/tg_send.sh"

BASE_URL="http://138.68.103.156:8001"

MIN_NET_ALERT_USD="${MIN_NET_ALERT_USD:-100}"

log() {
  echo "[$TS] $*" >> "$LOG_DIR/hohealth-alerts.log"
}

send_tg() {
  local msg="$1"
  if [[ -x "$TG_SEND" ]]; then
    "$TG_SEND" "$msg" || true
  else
    log "[warn] tg_send.sh missing or not executable"
  fi
}

# --- fetch endpoints (fail softly) ---
infra_txt=""
summary_txt=""
finance_txt=""

if infra_txt=$(curl -fsS --max-time 8 "$BASE_URL/txt/infra" 2>/dev/null); then
  :
else
  infra_txt=""
fi

if summary_txt=$(curl -fsS --max-time 8 "$BASE_URL/txt/summary" 2>/dev/null); then
  :
else
  summary_txt=""
fi

if finance_txt=$(curl -fsS --max-time 8 "$BASE_URL/txt/finance" 2>/dev/null); then
  :
else
  finance_txt=""
fi

# --- viewer / infra checks ---
if [[ -z "$infra_txt" ]]; then
  send_tg "⚠️ HANDS-OFF ALERT ($TS)
Viewer/infra endpoint unreachable at $BASE_URL.
Check: hoinfra / hosummary / hosnapshot"
  log "infra unreachable"
else
  health_ok=true

  if ! echo "$infra_txt" | grep -q 'health_status=healthy'; then
    health_ok=false
  fi
  if ! echo "$infra_txt" | grep -q 'infra_allow_trades=True'; then
    health_ok=false
  fi
  if echo "$infra_txt" | grep -q 'gate_blocked=True'; then
    health_ok=false
  fi

  if [[ "$health_ok" = false ]]; then
    send_tg "⚠️ INFRA STATUS ALERT ($TS)
Infra is not fully healthy.

Snippet:
/txt/infra ->
$(printf '%s\n' "$infra_txt" | head -n 20)"
    log "infra not healthy"
  fi
fi

# --- finance check: low total_usd ---
if [[ -n "$finance_txt" ]]; then
  total_line="$(printf '%s\n' "$finance_txt" | grep -i 'total_usd:' | head -n 1 || true)"
  if [[ -n "$total_line" ]]; then
    # extract like $1,500.00 -> 1500.00 -> 1500
    raw_amt="$(echo "$total_line" | sed -E 's/.*\$([0-9.,]+).*/\1/' | tr -d ',' || echo "")"
    int_amt="0"
    if [[ -n "$raw_amt" ]]; then
      int_amt="${raw_amt%.*}"
      [[ -z "$int_amt" ]] && int_amt="0"
    fi

    if [[ "$int_amt" =~ ^[0-9]+$ ]]; then
      if [ "$int_amt" -lt "$MIN_NET_ALERT_USD" ]; then
        send_tg "💸 LOW NET ALERT ($TS)
total_usd ~ \$$raw_amt (int=$int_amt) < floor=\$$MIN_NET_ALERT_USD

Snippet:
/txt/finance ->
$(printf '%s\n' "$finance_txt" | head -n 10)"
        log "low total_usd: $int_amt < $MIN_NET_ALERT_USD"
      fi
    else
      log "could not parse total_usd from: $total_line"
    fi
  else
    log "no total_usd line in finance_txt"
  fi
else
  log "finance_txt empty (viewer /txt/finance failed)"
fi

log "hohealth-alerts finished"
