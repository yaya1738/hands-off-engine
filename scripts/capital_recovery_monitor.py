#!/usr/bin/env python3
"""
Capital Recovery Monitor - Snowball Cycle 1
============================================

Monitors for capital recovery events:
1. Position resolutions returning funds
2. Balance threshold crossings
3. Trading capability restoration

When capital returns, automatically:
- Sends high-priority Telegram alert
- Updates system state
- Enables full trading mode
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

# Thresholds
MIN_TRADING_BALANCE = 50.0  # Minimum to start trading
OPTIMAL_TRADING_BALANCE = 200.0  # Target for full strategy

STATE_FILE = Path("/root/hands-off-engine/state/capital_recovery.json")
LOG_FILE = Path("/var/log/hands-off/capital_recovery.log")


def get_balance() -> float:
    """Get current Polymarket balance using trading safeguards method"""
    try:
        import sys
        sys.path.insert(0, '/root/hands-off-engine')
        from executor.trading_safeguards import TradingSafeguards

        safeguards = TradingSafeguards()
        # Check with 0 to just get balance info
        ok, msg = safeguards.check_wallet_balance(0)

        # Parse balance from message like "OK - balance: $8.99"
        if "balance: $" in msg:
            balance_str = msg.split("balance: $")[1].split()[0]
            return float(balance_str)
        elif "Insufficient balance: $" in msg:
            balance_str = msg.split("Insufficient balance: $")[1].split()[0]
            return float(balance_str)

    except Exception as e:
        print(f"Error getting balance: {e}")

    return 0.0


def load_state() -> dict:
    """Load previous state"""
    if STATE_FILE.exists():
        return json.load(open(STATE_FILE))
    return {
        "last_balance": 0.0,
        "last_check": None,
        "recovery_events": [],
        "trading_enabled": False,
        "alerts_sent": []
    }


def save_state(state: dict):
    """Save current state"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def send_telegram(message: str, priority: str = "normal"):
    """Send Telegram notification"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "8327766663")

    # Add priority emoji
    if priority == "high":
        message = "🚨🚨🚨\n" + message
    elif priority == "medium":
        message = "⚡\n" + message

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
        print(f"[TELEGRAM] Sent: {message[:50]}...")
    except Exception as e:
        print(f"Telegram error: {e}")


def log_event(event: str):
    """Log to file"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {event}\n")


def trigger_singularity_if_ready(balance: float):
    """Check and trigger singularity when threshold crossed"""
    if balance >= MIN_TRADING_BALANCE:
        try:
            import subprocess
            result = subprocess.run(
                ['python3', 'autonomous/singularity_trigger.py'],
                cwd='/root/hands-off-engine',
                capture_output=True,
                text=True,
                timeout=120
            )
            if 'SINGULARITY TRIGGERED' in result.stdout:
                print("[SINGULARITY] Trigger executed!")
        except Exception as e:
            print(f"[SINGULARITY] Error: {e}")


def check_recovery():
    """Main recovery check logic"""
    state = load_state()
    current_balance = get_balance()
    previous_balance = state.get("last_balance", 0.0)

    now = datetime.now(timezone.utc)
    print(f"[{now.isoformat()}] Balance: ${current_balance:.2f} (was ${previous_balance:.2f})")

    # Check for singularity trigger
    if current_balance >= MIN_TRADING_BALANCE and previous_balance < MIN_TRADING_BALANCE:
        print("[SINGULARITY] Trading threshold crossed! Triggering...")
        trigger_singularity_if_ready(current_balance)

    events = []

    # Check for significant balance increase (position resolution)
    balance_increase = current_balance - previous_balance
    if balance_increase > 10:  # $10+ increase indicates resolution
        event = {
            "type": "balance_increase",
            "timestamp": now.isoformat(),
            "previous": previous_balance,
            "current": current_balance,
            "increase": balance_increase
        }
        events.append(event)
        state["recovery_events"].append(event)

        log_event(f"BALANCE_INCREASE: +${balance_increase:.2f} (${previous_balance:.2f} -> ${current_balance:.2f})")

        # Alert based on new capability
        if current_balance >= OPTIMAL_TRADING_BALANCE:
            if "optimal_trading" not in state["alerts_sent"]:
                send_telegram(
                    f"*💰 CAPITAL RECOVERED - OPTIMAL*\n\n"
                    f"Balance: ${current_balance:.2f}\n"
                    f"Increase: +${balance_increase:.2f}\n\n"
                    f"🚀 *FULL TRADING CAPABILITY RESTORED*\n"
                    f"System will execute intelligent alpha signals.",
                    priority="high"
                )
                state["alerts_sent"].append("optimal_trading")
                state["trading_enabled"] = True

        elif current_balance >= MIN_TRADING_BALANCE:
            if "min_trading" not in state["alerts_sent"]:
                send_telegram(
                    f"*💵 CAPITAL RECOVERED - MINIMUM*\n\n"
                    f"Balance: ${current_balance:.2f}\n"
                    f"Increase: +${balance_increase:.2f}\n\n"
                    f"✓ Basic trading capability restored\n"
                    f"Target: ${OPTIMAL_TRADING_BALANCE:.0f} for full strategy",
                    priority="medium"
                )
                state["alerts_sent"].append("min_trading")
                state["trading_enabled"] = True

    # Check if balance dropped below threshold (loss detection)
    if previous_balance >= MIN_TRADING_BALANCE and current_balance < MIN_TRADING_BALANCE:
        log_event(f"BALANCE_DROP: ${previous_balance:.2f} -> ${current_balance:.2f}")
        state["trading_enabled"] = False
        # Reset alerts so they can fire again on recovery
        state["alerts_sent"] = []

    # Update state
    state["last_balance"] = current_balance
    state["last_check"] = now.isoformat()
    save_state(state)

    return {
        "balance": current_balance,
        "trading_enabled": state["trading_enabled"],
        "events": events
    }


def main():
    """Run recovery monitor"""
    # Load env
    env_file = Path("/root/hands-off-engine/.env.polymarket")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

    result = check_recovery()

    print(f"\nCapital Recovery Status:")
    print(f"  Balance: ${result['balance']:.2f}")
    print(f"  Trading Enabled: {result['trading_enabled']}")
    print(f"  Events: {len(result['events'])}")

    return result


if __name__ == "__main__":
    main()
