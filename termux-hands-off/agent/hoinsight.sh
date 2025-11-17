#!/usr/bin/env bash
# hoinsight - unified insight view
set -euo pipefail

ssh -T do138 <<'EOF'
python3 - <<'PY'
import json
import pathlib

BASE = pathlib.Path("/root/hands-off-out/state")

print("================ HANDS-OFF INSIGHT REPORT ================")

# ---------------- MODEL ----------------
model_file = BASE/"polymarket-model.json"
model = json.loads(model_file.read_text())
globals_cfg = model.get("globals", {})
events = model.get("events", [])

print("\n>>> MODEL SUMMARY")
print(f"  Budget USD         : {globals_cfg.get('budget_usd')}")
print(f"  Min edge to bet    : {globals_cfg.get('min_edge_to_bet_pct_points')} pp")
print(f"  Default stake      : {globals_cfg.get('default_stake_usd')} USD")
print(f"  Events configured  : {len(events)}")

for ev in events:
    print(f"   - {ev.get('id')}: price={ev.get('price')} edge={ev.get('edge_pct_points')}pp cap={ev.get('alloc',{}).get('max_usd')}")
    q = ev.get("question") or ev.get("meta",{}).get("question","")
    if q:
        print(f"       Q: {q}")

# ---------------- ORDERS ----------------
ofile = BASE/"decision_report.json"
dec = json.loads(ofile.read_text())
orders = dec.get("polymarket", {}).get("orders", [])

print("\n>>> CURRENT ORDERS")
print(f"  Orders count: {len(orders)}")
for o in orders:
    print(f"   - {o['side']} @ {o['limit_price']} on {o['market_id']}")
    print(f"       reason: {o.get('reason','')}")

print("\n==========================================================")
PY
EOF
