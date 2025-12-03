#!/usr/bin/env python3
"""
Auto-refresh balances for accounts we can read (blockchain wallets)
Run periodically to keep finance hub updated
"""

import json
import requests
from datetime import datetime
from pathlib import Path

FINANCE_HUB = Path(__file__).parent / "yair_finance_hub.json"

def get_erc20_balance(wallet, contract, rpc_url, decimals=6):
    """Fetch ERC20 token balance"""
    data = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{
            "to": contract,
            "data": f"0x70a08231000000000000000000000000{wallet[2:].lower()}"
        }, "latest"],
        "id": 1
    }
    try:
        resp = requests.post(rpc_url, json=data, timeout=10)
        result = resp.json()
        if "result" in result and result["result"] != "0x":
            balance_raw = int(result["result"], 16)
            return balance_raw / (10 ** decimals)
    except Exception as e:
        print(f"Error fetching balance: {e}")
    return None

def get_native_balance(wallet, rpc_url, decimals=18):
    """Fetch native token balance (ETH, MATIC, etc)"""
    data = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet, "latest"],
        "id": 1
    }
    try:
        resp = requests.post(rpc_url, json=data, timeout=10)
        result = resp.json()
        if "result" in result:
            balance_raw = int(result["result"], 16)
            return balance_raw / (10 ** decimals)
    except Exception as e:
        print(f"Error fetching native balance: {e}")
    return None

def refresh():
    """Refresh all readable balances"""
    with open(FINANCE_HUB) as f:
        hub = json.load(f)
    
    now = datetime.utcnow().isoformat() + "Z"
    updated = False
    
    # Polymarket wallet (Polygon USDC)
    pm_wallet = hub["accounts"]["polymarket"].get("wallet_address")
    if pm_wallet:
        usdc = get_erc20_balance(
            pm_wallet,
            "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC on Polygon
            "https://polygon-rpc.com",
            decimals=6
        )
        if usdc is not None:
            hub["accounts"]["polymarket"]["balance_usdc"] = usdc
            hub["accounts"]["polymarket"]["last_updated"] = now
            print(f"✅ Polymarket USDC: ${usdc:.2f}")
            updated = True
        
        # Also get MATIC for gas
        matic = get_native_balance(pm_wallet, "https://polygon-rpc.com")
        if matic is not None:
            hub["accounts"]["polymarket"]["balance_matic"] = matic
            print(f"   MATIC (gas): {matic:.4f}")
    
    if updated:
        hub["last_updated"] = now
        with open(FINANCE_HUB, 'w') as f:
            json.dump(hub, f, indent=2)
        print(f"\n✅ Finance hub updated at {now}")
    else:
        print("No updates made")

if __name__ == "__main__":
    refresh()
