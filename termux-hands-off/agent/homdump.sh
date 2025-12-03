#!/usr/bin/env bash
# homdump - dump full JSON for markets matching an id or keyword
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: homdump <query_or_id>"
  echo "  example: homdump 0x41190eb9..."
  echo "           homdump 'trump win iowa'"
  exit 1
fi

QUERY="$*"

ssh do138 python3 - "$QUERY" <<'PY'
import json, pathlib, sys

BASE = pathlib.Path("/root/hands-off-out/state")
COMPACT = BASE / "polymarket-compact.json"

if len(sys.argv) < 2:
    print("[err] missing query argument")
    raise SystemExit(1)

query = sys.argv[1].strip().lower()
if not query:
    print("[err] empty query")
    raise SystemExit(1)

try:
    data = json.loads(COMPACT.read_text())
except FileNotFoundError:
    print("[err] polymarket-compact.json not found on droplet")
    raise SystemExit(1)
except Exception as e:
    print(f"[err] failed to parse polymarket-compact.json: {e}")
    raise SystemExit(1)

hits = []
for mid, m in data.items():
    q = (m.get("question") or "").lower()
    cat = (m.get("category") or "").lower()
    if (
        query in mid.lower()
        or query in q
        or query in cat
    ):
        hits.append(m)

print(f"query={query!r} matches={len(hits)} (showing up to 3)")

for i, m in enumerate(hits[:3], 1):
    print(f"\n--- match #{i} id={m.get('id')}")
    print(json.dumps(m, indent=2, sort_keys=True))
PY
