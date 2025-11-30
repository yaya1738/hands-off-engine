#!/usr/bin/env python3
"""
Payment Monitor - Snowball Cycle 2
==================================

Monitors the wallet for incoming USDC payments.
Alerts when new funds arrive (potential client payment).
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import os
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

WALLET = "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # Native USDC on Polygon
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # Bridged USDC

STATE_FILE = Path("/root/hands-off-engine/state/payment_monitor.json")


def get_token_balance(wallet: str, contract: str) -> float:
    """Get ERC20 token balance from Polygon RPC"""
    # balanceOf(address) selector
    data = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{
            "to": contract,
            "data": f"0x70a08231000000000000000000000000{wallet[2:]}"
        }, "latest"],
        "id": 1
    }

    try:
        resp = requests.post(
            "https://polygon-rpc.com",
            json=data,
            timeout=10
        )
        result = resp.json().get("result", "0x0")
        balance_wei = int(result, 16)
        return balance_wei / 1e6  # USDC has 6 decimals
    except Exception as e:
        print(f"Error: {e}")
        return 0.0


def send_telegram(message: str):
    """Send Telegram notification"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "8327766663")

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram error: {e}")


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.load(open(STATE_FILE))
    return {"last_balance": 0.0, "last_check": None, "payments": []}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def main():
    state = load_state()

    # Get current balances
    native = get_token_balance(WALLET, USDC_CONTRACT)
    bridged = get_token_balance(WALLET, USDC_BRIDGED)
    total = native + bridged

    previous = state.get("last_balance", 0.0)
    now = datetime.now(timezone.utc)

    print(f"[{now.isoformat()}] USDC Balance: ${total:.2f} (native: ${native:.2f}, bridged: ${bridged:.2f})")
    print(f"  Previous: ${previous:.2f}")

    # Check for significant increase (payment received)
    increase = total - previous
    if increase >= 10:  # $10+ increase = likely payment
        payment = {
            "timestamp": now.isoformat(),
            "amount": increase,
            "previous_balance": previous,
            "new_balance": total
        }
        state["payments"].append(payment)

        send_telegram(
            f"*💵 PAYMENT RECEIVED*\n\n"
            f"Amount: +${increase:.2f}\n"
            f"New Balance: ${total:.2f}\n"
            f"Time: {now.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"_Check for client correspondence!_"
        )

        print(f"  [ALERT] Payment detected: +${increase:.2f}")

    state["last_balance"] = total
    state["last_check"] = now.isoformat()
    save_state(state)


if __name__ == "__main__":
    main()
