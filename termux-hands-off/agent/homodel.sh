#!/usr/bin/env bash
# homodel - show polymarket-model.json (globals + events)
set -euo pipefail

REMOTE="do138"

echo "================ POLYMARKET MODEL =================="
ssh "$REMOTE" "python3 - <<'PY'
from pathlib import Path
import json

# Hardcoded path on droplet
path = Path('/root/hands-off-out/state/polymarket-model.json')

try:
    text = path.read_text(encoding='utf-8')
except FileNotFoundError:
    print(f'[error] polymarket-model.json not found at {path}')
    raise SystemExit(0)
except Exception as e:
    print(f'[error] failed to read {path}: {e}')
    raise SystemExit(1)

try:
    data = json.loads(text)
except Exception as e:
    print(f'[error] failed to parse polymarket-model.json: {e}')
    raise SystemExit(1)

globals_cfg = data.get('globals') or {}
events = data.get('events') or []

print('--- GLOBALS ---')
for k in sorted(globals_cfg):
    print(f'{k}: {globals_cfg[k]}')
print()

print(f'--- EVENTS ({len(events)}) ---')
for ev in events:
    ev_id = ev.get('id') or 'UNKNOWN'
    side = ev.get('side', 'YES')
    price = ev.get('price')
    edge = ev.get('edge_pct_points')
    alloc = (ev.get('alloc') or {}).get('max_usd')
    q = ev.get('question') or ev.get('meta', {}).get('question') or ''
    print(f'id={ev_id}')
    print(f'  side={side} price={price} edge_pp={edge} max_usd={alloc}')
    if q:
        short_q = q if len(q) <= 100 else q[:97] + '...'
        print(f'  Q: {short_q}')
    print()
PY"
echo "===================================================="
