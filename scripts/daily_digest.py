#!/usr/bin/env python3
"""
Daily Digest - Snowball Cycle 3
===============================

Sends a comprehensive daily summary at 8am including:
- Financial status
- Position updates
- System health
- Recent events
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
import sys
import json
import requests
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/root/hands-off-engine')


def get_balance() -> float:
    """Get current balance"""
    try:
        from executor.trading_safeguards import TradingSafeguards
        safeguards = TradingSafeguards()
        ok, msg = safeguards.check_wallet_balance(0)
        if "balance: $" in msg:
            return float(msg.split("balance: $")[1].split()[0])
        elif "Insufficient balance: $" in msg:
            return float(msg.split("Insufficient balance: $")[1].split()[0])
    except:
        pass
    return 0.0


def get_position_values() -> dict:
    """Get current position values"""
    positions = {
        "fed-rate-hike-in-2025": {"shares": 4776, "side": "YES"},
        "sundar-pichai-out-as-google-ceo-in-2025": {"shares": 1356, "side": "YES"},
        "will-6-fed-rate-cuts-happen-in-2025": {"shares": 25000, "side": "YES"},
        "will-7-fed-rate-cuts-happen-in-2025": {"shares": 50000, "side": "YES"},
    }

    total = 0.0
    details = []

    for slug, pos in positions.items():
        try:
            resp = requests.get(
                f"https://gamma-api.polymarket.com/markets?slug={slug}",
                timeout=10
            )
            data = resp.json()
            if data:
                prices = json.loads(data[0].get("outcomePrices", '["0","0"]'))
                price = float(prices[0])
                value = pos["shares"] * price
                total += value
                details.append({"slug": slug[:30], "value": value, "price": price})
        except:
            pass

    return {"total": total, "details": details}


def get_days_until_resolution() -> dict:
    """Calculate days until position resolutions"""
    now = datetime.now(timezone.utc)
    dec10 = datetime(2025, 12, 10, 12, 0, 0, tzinfo=timezone.utc)
    dec31 = datetime(2025, 12, 31, 12, 0, 0, tzinfo=timezone.utc)

    return {
        "dec10": (dec10 - now).days,
        "dec31": (dec31 - now).days
    }


def get_recent_events() -> list:
    """Get recent events from logs"""
    events = []

    # Check capital recovery log
    log_file = Path("/var/log/hands-off/capital_recovery.log")
    if log_file.exists():
        lines = log_file.read_text().splitlines()[-5:]
        for line in lines:
            if "BALANCE_INCREASE" in line or "ALERT" in line:
                events.append(line[:100])

    # Check payment log
    payment_log = Path("/var/log/hands-off/payment_monitor.log")
    if payment_log.exists():
        lines = payment_log.read_text().splitlines()[-5:]
        for line in lines:
            if "Payment detected" in line:
                events.append(line[:100])

    return events[-3:] if events else ["No significant events"]


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
        print("Digest sent")
    except Exception as e:
        print(f"Error: {e}")


def main():
    # Gather data
    balance = get_balance()
    positions = get_position_values()
    days = get_days_until_resolution()
    events = get_recent_events()

    total_value = balance + positions["total"]

    # Build digest
    digest = f"""📊 *DAILY DIGEST*
{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

*Financial Status:*
• Balance: ${balance:.2f}
• Positions: ${positions['total']:.2f}
• Total: ${total_value:.2f}

*Resolution Countdown:*
• Dec 10 (Fed): {days['dec10']} days
• Dec 31 (Pichai): {days['dec31']} days

*Trading Status:*
{'✅ Enabled' if balance >= 50 else '⏸️ Paused (need $50+)'}

*Recent Events:*
"""
    for event in events:
        digest += f"• {event[:50]}\n"

    digest += """
*Live Pages:*
• :8080 - Affiliate
• :8081 - Consulting

_System running autonomously._"""

    send_telegram(digest)

    # Log
    print(f"Balance: ${balance:.2f}")
    print(f"Positions: ${positions['total']:.2f}")
    print(f"Days to Dec 10: {days['dec10']}")


if __name__ == "__main__":
    # Load env
    env_file = Path("/root/hands-off-engine/.env.polymarket")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

    main()
