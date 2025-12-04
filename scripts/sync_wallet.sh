#!/bin/bash
# INTEGRAFIX: Wallet State Sync
# Syncs real Polymarket wallet state to local files

cd /root/hands-off-engine
export $(grep -v '^#' .env.polymarket | xargs) 2>/dev/null

PYTHONPATH=/root/hands-off-engine python3 << 'EOF'
import os
import json
from pathlib import Path
from datetime import datetime, timezone

try:
    from py_clob_client.client import ClobClient

    key = os.environ.get('POLYMARKET_PRIVATE_KEY', '')
    if not key:
        print("No API key")
        exit(1)

    client = ClobClient('https://clob.polymarket.com', key=key, chain_id=137)
    creds = client.create_or_derive_api_creds()
    client.set_api_creds(creds)

    addr = client.get_address()
    orders = client.get_orders()

    buy_total = sum(float(o.get('original_size', 0)) for o in orders if o.get('side') == 'BUY')
    sell_total = sum(float(o.get('original_size', 0)) for o in orders if o.get('side') == 'SELL')

    now = datetime.now(timezone.utc).isoformat()

    # Update wallet_state.json
    state = {
        'address': addr,
        'open_orders': len(orders),
        'buy_total': buy_total,
        'sell_total': sell_total,
        'total_value': buy_total + sell_total,
        'last_sync': now,
        'orders': [
            {
                'side': o.get('side'),
                'size': float(o.get('original_size', 0)),
                'price': float(o.get('price', 0)),
                'status': o.get('status')
            }
            for o in orders
        ]
    }

    with open('state/wallet_state.json', 'w') as f:
        json.dump(state, f, indent=2)

    print(f"[{now[:19]}] Synced: {len(orders)} orders, ${buy_total + sell_total:.2f} total")

except Exception as e:
    print(f"Sync error: {e}")
EOF
