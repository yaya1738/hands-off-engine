#!/usr/bin/env python3
"""
Position Price Monitor - Alert on significant price movements

Checks current positions and alerts via Telegram if prices spike.
Also alerts when positions are approaching resolution date.
Designed to catch tail bet opportunities to exit profitably.
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
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


def get_market_info(slug: str) -> dict:
    """Fetch market price and metadata"""
    try:
        resp = requests.get(
            f"https://gamma-api.polymarket.com/markets?slug={slug}",
            timeout=10
        )
        data = resp.json()
        if data:
            market = data[0]
            prices = json.loads(market.get("outcomePrices", '["0","0"]'))
            return {
                "price": float(prices[0]),
                "end_date": market.get("endDate"),
                "closed": market.get("closed", False),
                "question": market.get("question", slug),
            }
    except Exception as e:
        print(f"Error fetching {slug}: {e}")
    return {"price": 0.0, "end_date": None, "closed": False, "question": slug}


def get_market_price(slug: str) -> float:
    """Fetch current YES price for a market (legacy wrapper)"""
    return get_market_info(slug).get("price", 0.0)


def send_telegram(message: str):
    """Send alert via Telegram using system notify"""
    # Try the termux notify.py first (has config)
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "termux-hands-off/agent/notify.py"],
            input=message,
            capture_output=True,
            text=True,
            cwd="/root/hands-off-engine",
            timeout=30
        )
        if result.returncode == 0:
            print(f"[TELEGRAM] Sent: {message[:50]}...")
            return
    except Exception as e:
        pass

    # Fallback to env vars
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[ALERT - NO TELEGRAM] {message}")
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


def check_resolution_approaching(state: dict) -> list:
    """Check if any positions are approaching resolution"""
    resolution_alerts = []
    now = datetime.now(timezone.utc)

    for pos in POSITIONS:
        info = get_market_info(pos["slug"])
        if not info["end_date"]:
            continue

        try:
            end_dt = datetime.fromisoformat(info["end_date"].replace("Z", "+00:00"))
            days_left = (end_dt - now).days

            # Alert milestones: 7 days, 3 days, 1 day, 0 days (resolution day)
            alert_days = [7, 3, 1, 0]

            for milestone in alert_days:
                if days_left <= milestone:
                    # Check if we already alerted for this milestone
                    alert_key = f"{pos['slug']}_resolution_{milestone}"
                    if alert_key not in state.get("resolution_alerts", []):
                        resolution_alerts.append({
                            "slug": pos["slug"],
                            "days_left": days_left,
                            "milestone": milestone,
                            "end_date": info["end_date"],
                            "question": info["question"],
                            "current_price": info["price"],
                            "shares": pos["shares"],
                            "alert_key": alert_key,
                        })
                    break  # Only alert for closest milestone
        except Exception as e:
            print(f"Error parsing date for {pos['slug']}: {e}")

    return resolution_alerts


def main():
    state = load_state()
    if "resolution_alerts" not in state:
        state["resolution_alerts"] = []

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

    # Check resolution dates
    resolution_alerts = check_resolution_approaching(state)

    if alerts:
        msg = "🚨 *POSITION ALERT*\n\n"
        for a in alerts:
            msg += f"*{a['slug']}*\n"
            msg += f"  YES: {a['price']:.2%} (threshold: {a['threshold']:.1%})\n"
            msg += f"  Value: ${a['value']:.2f}\n"
            msg += f"  PnL: {a['pnl_pct']:+.1f}%\n\n"
        msg += "_Consider selling if spike is temporary_"
        send_telegram(msg)

    if resolution_alerts:
        msg = "⏰ *RESOLUTION APPROACHING*\n\n"
        for r in resolution_alerts:
            if r["days_left"] <= 0:
                msg += f"🔔 *{r['question'][:50]}*\n"
                msg += f"   RESOLVING TODAY!\n"
            else:
                msg += f"📅 *{r['question'][:50]}*\n"
                msg += f"   {r['days_left']} days until resolution\n"
            msg += f"   Current: {r['current_price']:.2%} YES\n"
            msg += f"   Shares: {r['shares']:,}\n\n"
            state["resolution_alerts"].append(r["alert_key"])
        send_telegram(msg)

    if alerts or resolution_alerts:
        save_state(state)

    print(f"\nChecked {len(POSITIONS)} positions, {len(alerts)} price alerts, {len(resolution_alerts)} resolution alerts")


if __name__ == "__main__":
    main()
