#!/usr/bin/env bash
# hopricesync - sync Polymarket compact→model prices and refresh orders
set -euo pipefail

REMOTE="do138"

ssh "$REMOTE" <<'EOF'
set -euo pipefail
BASE="/root/hands-off-out/state"

PRICE_FILE="$BASE/polymarket-compact.json"
MODEL_FILE="$BASE/polymarket-model.json"

if [ ! -f "$PRICE_FILE" ] || [ ! -f "$MODEL_FILE" ]; then
  echo "[err] Missing compact or model file"
  exit 1
fi

echo "[info] loading compact + model"
python3 <<'PY'
import json, pathlib

base = pathlib.Path("/root/hands-off-out/state")

compact = json.loads((base/"polymarket-compact.json").read_text())
model   = json.loads((base/"polymarket-model.json").read_text())

prices = {}
for group in compact.get("groups", []):
    for m in group.get("markets", []):
        prices[m["id"]] = m.get("price", 0)

changed = []
for ev in model.get("events", []):
    mid = ev.get("id")
    if mid in prices:
        old = ev.get("price")
        new = prices[mid]
        if old != new:
            ev["price"] = new
            changed.append((mid, old, new))

if changed:
    print("[update] prices changed:")
    for mid, old, new in changed:
        print(f" - {mid}: {old} -> {new}")
else:
    print("[update] no price changes")

(base/"polymarket-model.json").write_text(
    json.dumps(model, indent=2, sort_keys=True)
)
PY

echo "[kick] ho-decision-infra"
python3 /usr/local/bin/ho-decision-infra.py || true

echo "[kick] ho_add_test_orders"
python3 /usr/local/bin/ho_add_test_orders.py || true

echo "[kick] ho_executor_plan"
python3 /usr/local/bin/ho_executor_plan.py || true

EOF

echo "[done] hopricesync completed"
