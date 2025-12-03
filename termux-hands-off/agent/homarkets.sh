#!/usr/bin/env bash
# homarkets - show live Polymarket universe from polymarket-compact.json
set -euo pipefail

REMOTE="do138"
COMPACT="/root/hands-off-out/state/polymarket-compact.json"

ssh "$REMOTE" "python3 - << 'PY'
from pathlib import Path
import json
from collections import defaultdict

path = Path('$COMPACT')
try:
    data = json.loads(path.read_text(encoding='utf-8'))
except FileNotFoundError:
    print('[error] polymarket-compact.json not found at', path)
    raise SystemExit(0)
except Exception as e:
    print('[error] failed to parse polymarket-compact.json:', e)
    raise SystemExit(1)

if not isinstance(data, dict):
    print('[warn] unexpected compact format, type =', type(data).__name__)
    try:
        print('len(data) =', len(data))
    except Exception:
        pass
    raise SystemExit(0)

groups = defaultdict(list)
for m in data.values():
    cat = (m.get('category') or 'other').upper()
    groups[cat].append(m)

total = sum(len(v) for v in groups.values())
print('total_markets:', total)

if total == 0:
    print('\\n(no markets found in compact file)')
    raise SystemExit(0)

for cat in sorted(groups):
    bucket = groups[cat][:10]
    print(f\"\\n--- {cat} (showing up to 10 of {len(groups[cat])}) ---\")
    for m in bucket:
        mid = (m.get('id') or '')[:16]
        price = m.get('price', 0.0)
        try:
            price = float(price)
        except Exception:
            price = 0.0
        q = (m.get('question') or '').strip()
        if len(q) > 100:
            q = q[:97] + '...'
        print(f\"- {mid} @ {price:.3f}\")
        print(f\"  Q: {q.lower()}\")
PY"
