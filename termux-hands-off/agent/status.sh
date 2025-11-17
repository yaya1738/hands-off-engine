#!/data/data/com.termux/files/usr/bin/bash
set -e
JSON="$HOME/hands-off/state/finance.json"
OUT="$HOME/hands-off/state/decision_output.json"
PNS="$HOME/hands-off/state/pnl_summary.json"
HIS="$HOME/hands-off/state/pnl_history.json"

# Ensure fresh state + PnL
bash "$HOME/hands-off/agent/compute_pnl.sh" >/dev/null 2>&1 || true

echo "---- balances ----"
jq -C '.balances' "$JSON" 2>/dev/null || echo "(no finance.json yet)"

echo
echo "---- recommendation ----"
jq -C '{ts, weights, recommend}' "$OUT" 2>/dev/null || echo "(no decision_output.json yet)"

echo
echo "---- PnL ----"
if [ -f "$PNS" ]; then
  # print compact PnL summary
  jq -C 'def pct(p): (if p==null then "-" else ((p|tonumber)|round*1.0) end);
    {
      total_usd: .total_usd,
      since_last: {delta: .delta_since_last.delta, pct: .delta_since_last.pct},
      last_24h:   {delta: .delta_24h.delta,        pct: .delta_24h.pct},
      last_7d:    {delta: .delta_7d.delta,         pct: .delta_7d.pct}
    }' "$PNS"
else
  echo "(no pnl_summary.json yet)"
fi
