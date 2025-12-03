#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"
STATE="/root/hands-off-out/state"
DECISION="$STATE/decision_report.json"

echo "================ HANDS-OFF ORDERS ================"

ssh "$REMOTE" "python3 - <<PY
from pathlib import Path
import json

path = Path('$DECISION')
try:
    data = json.loads(path.read_text(encoding='utf-8'))
except FileNotFoundError:
    print('[error] decision_report.json not found at', path)
    raise SystemExit(0)
except Exception as e:
    print('[error] failed to parse decision_report.json:', e)
    raise SystemExit(0)

polymarket = data.get('polymarket') or {}
orders = polymarket.get('orders') or []

infra_allow = data.get('infra_allow_trades')
gate_blocked = data.get('gate_blocked')
as_of = data.get('as_of')

print('as_of         :', as_of)
print('infra_allow   :', infra_allow)
print('gate_blocked  :', gate_blocked)
print('orders_count  :', len(orders))
print()

if not orders:
    print('[info] no polymarket.orders in decision_report.json')
else:
    for i, o in enumerate(orders, 1):
        market_id = o.get('market_id') or o.get('id') or 'UNKNOWN'
        side = o.get('side') or o.get('direction') or 'UNKNOWN'
        stake = o.get('stake_usd') or 0.0
        price = o.get('limit_price') or o.get('price') or 0.0
        reason = o.get('reason') or ''
        question = o.get('question') or o.get('meta', {}).get('question') or ''

        print(f'[{i}] {side} {stake:.2f} @ {price:.4f} on {market_id}')
        if question:
            print(f'    Q: {question}')
        if reason:
            print(f'    reason: {reason}')
        print()
PY"
echo "==================================================="
