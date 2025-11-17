#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

echo "================ HANDS-OFF DASHBOARD ================"
echo
echo ">>> INFRA + HEALTH (remote)"
ssh "$REMOTE" '
  set -e
  STATE="/root/hands-off-out/state"

  echo
  echo "--- infra.txt (top) ---"
  sed -n "1,40p" "$STATE/infra.txt" 2>/dev/null || echo "no infra.txt"

  echo
  echo "--- health.json ---"
  sed -n "1,40p" "$STATE/health.json" 2>/dev/null || echo "no health.json"
'

echo
echo ">>> FINANCE (remote summary)"
ssh "$REMOTE" '
  set -e
  STATE="/root/hands-off-out/state"
  if [ -f "$STATE/finance_report.json" ]; then
    python3 - <<PY
import json, pathlib
p = pathlib.Path("$STATE/finance_report.json")
data = json.loads(p.read_text())
print("updated:", data.get("updated"))
print("total_usd:", data.get("total_usd"))
print("delta_usd:", data.get("delta_usd"))
print("accounts:")
for a in data.get("accounts", []):
    print("  - {name:20s} {bal:,.2f} {cur}".format(
        name=a.get("name",""),
        bal=a.get("balance",0.0),
        cur=a.get("currency","")
    ))
PY
  else
    echo "no finance_report.json"
  fi
'

echo
echo ">>> EXECUTOR STATUS (remote)"
ssh "$REMOTE" '
  set -e
  STATE="/root/hands-off-out/state"
  REP="$STATE/executor_report.json"
  if [ -f "$REP" ]; then
    python3 - <<PY
import json, pathlib
p = pathlib.Path("$REP")
data = json.loads(p.read_text())
print("as_of         :", data.get("as_of"))
print("effective_mode:", data.get("effective_mode"))
print("gate_blocked  :", data.get("gate_blocked"))
print("infra_allow   :", data.get("infra_allow_trades"))
print("killswitch    :", data.get("killswitch_present"))
print("live_enabled  :", data.get("live_enabled"))
print("mode_reason   :", data.get("mode_reason"))
PY
  else
    echo "no executor_report.json"
  fi
'

echo
echo "====================================================="
