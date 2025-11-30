#!/usr/bin/env python3
"""
Position Price Monitor - Alert on significant price movements

Checks current positions and alerts via Telegram if prices spike.
Designed to catch tail bet opportunities to exit profitably.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Our positions from Nov 28 trades
POSITIONS = [
    {
        "slug": "fed-rate-hike-in-2025",
        "side": "YES",
        "shares": 4776,
        "cost_basis": 50,
        "alert_threshold": 0.03,  # Alert if YES > 3% (was 1%)
    },
    {
        "slug": "sundar-pichai-out-as-google-ceo-in-2025",
        "side": "YES",
        "shares": 1356,
        "cost_basis": 50,
        "alert_threshold": 0.05,  # Alert if YES > 5% (was 3.7%)
    },
    {
        "slug": "will-6-fed-rate-cuts-happen-in-2025",
        "side": "YES",
        "shares": 25000,
        "cost_basis": 50,
        "alert_threshold": 0.01,  # Alert if > 1% (currently 0.05%)
    },
    {
        "slug": "will-7-fed-rate-cuts-happen-in-2025",
        "side": "YES",
        "shares": 50000,
        "cost_basis": 50,
        "alert_threshold": 0.01,
    },
]

STATE_FILE = Path("/root/hands-off-engine/state/position_alerts.json")


def get_market_price(slug: str) -> float:
    """Fetch current YES price for a market"""
    try:
        resp = requests.get(
            f"https://gamma-api.polymarket.com/markets?slug={slug}",
            timeout=10
        )
        data = resp.json()
        if data:
            prices = json.loads(data[0].get("outcomePrices", '["0","0"]'))
            return float(prices[0])
    except Exception as e:
        print(f"Error fetching {slug}: {e}")
    return 0.0


def send_telegram(message: str):
    """Send alert via Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[ALERT] {message}")
        return
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
    return {"last_alerts": {}}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(state, open(STATE_FILE, "w"), indent=2)


def main():
    state = load_state()
    alerts = []
    
    for pos in POSITIONS:
        price = get_market_price(pos["slug"])
        if price <= 0:
            continue
            
        value = pos["shares"] * price
        pnl = value - pos["cost_basis"]
        pnl_pct = (pnl / pos["cost_basis"]) * 100
        
        print(f"{pos['slug'][:40]:40} YES={price:.4f} Value=${value:.2f} PnL={pnl_pct:+.1f}%")
        
        # Check if price crossed threshold
        if price >= pos["alert_threshold"]:
            last_alert = state["last_alerts"].get(pos["slug"], 0)
            # Only alert if price increased 50%+ since last alert
            if price > last_alert * 1.5 or last_alert == 0:
                alerts.append({
                    "slug": pos["slug"],
                    "price": price,
                    "value": value,
                    "pnl_pct": pnl_pct,
                    "threshold": pos["alert_threshold"],
                })
                state["last_alerts"][pos["slug"]] = price
    
    if alerts:
        msg = "🚨 *POSITION ALERT*\n\n"
        for a in alerts:
            msg += f"*{a['slug']}*\n"
            msg += f"  YES: {a['price']:.2%} (threshold: {a['threshold']:.1%})\n"
            msg += f"  Value: ${a['value']:.2f}\n"
            msg += f"  PnL: {a['pnl_pct']:+.1f}%\n\n"
        msg += "_Consider selling if spike is temporary_"
        send_telegram(msg)
        save_state(state)
    
    print(f"\nChecked {len(POSITIONS)} positions, {len(alerts)} alerts triggered")


if __name__ == "__main__":
    main()
