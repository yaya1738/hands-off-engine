#!/usr/bin/env bash
# homatch - search polymarket-compact.json on the droplet
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: homatch <keyword> [limit]"
  exit 1
fi

QUERY="$1"
LIMIT="${2:-20}"

ssh do138 python3 - "$QUERY" "$LIMIT" <<'PY'
import json, sys
from pathlib import Path

STATE = Path("/root/hands-off-out/state")
COMPACT = STATE / "polymarket-compact.json"

if len(sys.argv) < 3:
    print("internal error: missing argv")
    raise SystemExit(1)

query = sys.argv[1].lower()
limit = int(sys.argv[2])

try:
    data = json.loads(COMPACT.read_text(encoding="utf-8"))
except FileNotFoundError:
    print("[error] polymarket-compact.json not found")
    raise SystemExit(1)
except Exception as e:
    print(f"[error] failed to read/parse compact file: {e}")
    raise SystemExit(1)

matches = []
for mid, m in data.items():
    q = (m.get("question") or "").lower()
    cat = (m.get("category") or "").lower()
    if query in q or query in cat:
        m = dict(m)
        m["id"] = mid
        matches.append(m)

print(f"query='{query}' matches={len(matches)} (showing up to {limit})")
for m in matches[:limit]:
    mid = m.get("id")
    price = m.get("price")
    cat = m.get("category")
    q = (m.get("question") or "").strip()
    short_q = q if len(q) <= 100 else q[:97] + "..."
    try:
        p_str = f"{float(price):.3f}"
    except Exception:
        p_str = str(price)
    print(f"- {mid} @ {p_str} cat={cat} Q={short_q}")
PY
