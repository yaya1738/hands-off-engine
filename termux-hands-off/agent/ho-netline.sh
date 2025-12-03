#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"
STATE="/root/hands-off-out/state"

# 1) Fetch JSON from droplet
dec_json="$(ssh "$REMOTE" "cat $STATE/decision_report.json 2>/dev/null" || echo '')"
fin_json="$(ssh "$REMOTE" "cat $STATE/finance_report.json 2>/dev/null" || echo '')"

if [ -z "$dec_json" ] && [ -z "$fin_json" ]; then
  echo "net=$0.00 | cash=$0.00, crypto=$0.00, polymarket=$0.00 (no remote data)"
  exit 0
fi

# 2) Recommended buckets from decision_report.json (fallback to 0, never null)
cash="$(printf '%s\n' "$dec_json" | jq -r '.recommend.cash // 0' 2>/dev/null || echo 0)"
crypto="$(printf '%s\n' "$dec_json" | jq -r '.recommend.crypto // 0' 2>/dev/null || echo 0)"
polymarket="$(printf '%s\n' "$dec_json" | jq -r '.recommend.polymarket // 0' 2>/dev/null || echo 0)"

# 3) If recommend block is missing/empty, fall back to finance_report total_usd
if [ "$cash" = "0" ] && [ "$crypto" = "0" ] && [ "$polymarket" = "0" ]; then
  total="$(printf '%s\n' "$fin_json" | jq -r '.total_usd // 0' 2>/dev/null || echo 0)"
  cash="$total"
fi

# 4) Compute net = cash + crypto + polymarket safely
net="$(python3 - <<PY
c = float("${cash:-0}")
x = float("${crypto:-0}")
p = float("${polymarket:-0}")
print(c + x + p)
PY
)"

# 5) Pretty-print line
printf 'net=$%.2f | cash=$%.2f, crypto=$%.2f, polymarket=$%.2f\n' "$net" "$cash" "$crypto" "$polymarket"
