#!/usr/bin/env bash
# hoaddmodel - promote a Polymarket market from compact.json into polymarket-model.json
# Usage:
#   hoaddmodel <market_id> [edge_pp] [max_usd]
#
# Example:
#   hoaddmodel 0xc03f3229... 5 20

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: hoaddmodel <market_id> [edge_pp] [max_usd]"
  echo "  example: hoaddmodel 0xc03f3229... 5 20"
  exit 1
fi

MID="$1"
EDGE="${2:-0}"
CAP="${3:-0}"

ssh do138 python3 - "$MID" "$EDGE" "$CAP" <<'PY'
import json, sys, pathlib

STATE = pathlib.Path("/root/hands-off-out/state")
MODEL = STATE / "polymarket-model.json"
COMPACT = STATE / "polymarket-compact.json"

if len(sys.argv) < 4:
    print("[err] need market_id, edge_pp, max_usd")
    raise SystemExit(1)

mid = sys.argv[1]
edge_pp = float(sys.argv[2])
max_usd = float(sys.argv[3])

# --- load compact universe ---
try:
    compact = json.loads(COMPACT.read_text())
except FileNotFoundError:
    print("[err] polymarket-compact.json not found")
    raise SystemExit(1)

m = compact.get(mid)
if not m:
    print(f"[err] market {mid} not found in compact")
    raise SystemExit(1)

price = float(m.get("price") or 0.0)
question = m.get("question") or ""
category = m.get("category") or "ALL"

# --- load or init model ---
if MODEL.exists():
    data = json.loads(MODEL.read_text())
else:
    data = {
        "as_of": None,
        "globals": {
            "budget_usd": 30.0,
            "default_stake_usd": 5.0,
            "min_edge_to_bet_pct_points": 3.0,
        },
        "events": [],
    }

events = data.setdefault("events", [])

# upsert event
existing = None
for ev in events:
    if ev.get("id") == mid:
        existing = ev
        break

if existing is None:
    ev = {
        "id": mid,
        "side": "YES",
        "price": price,
        "edge_pct_points": edge_pp,
        "question": question,
        "category": category,
        "alloc": {"max_usd": max_usd},
    }
    events.append(ev)
    action = "added"
else:
    existing["price"] = price
    existing["edge_pct_points"] = edge_pp
    existing.setdefault("alloc", {})["max_usd"] = max_usd
    existing["question"] = question or existing.get("question")
    existing["category"] = category
    action = "updated"

MODEL.write_text(json.dumps(data, indent=2, sort_keys=True))
print(f"[ok] {action} model event id={mid}")
print(f"     price={price} edge_pp={edge_pp} max_usd={max_usd}")
PY
