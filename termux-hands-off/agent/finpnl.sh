#!/data/data/com.termux/files/usr/bin/bash
set -e
PNS="$HOME/hands-off/state/pnl_summary.json"
if [ ! -s "$PNS" ]; then
  echo "(no pnl_summary.json yet)"
  exit 0
fi
jq -r '
  def S: if .==null then "-" else tostring end;
  [
    (.ts|todate),
    (.total_usd | S),
    (.delta_since_last.delta | S), (.delta_since_last.pct | S),
    (.delta_24h.delta | S),        (.delta_24h.pct | S),
    (.delta_7d.delta | S),         (.delta_7d.pct | S)
  ] | @tsv
' "$PNS"
