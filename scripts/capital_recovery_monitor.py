#!/usr/bin/env python3
"""
Capital Recovery Monitor - Snowball Cycle 1
============================================

Read-only monitor for verified capital changes.
It never enables trading, starts orders, or treats a balance threshold as authorization.
"""

# UNIFIED AI - All systems serve the configured operator
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = os.getenv("HANDS_OFF_OWNER_NAME", "Configured operator")


import json
import requests
from datetime import datetime, timezone
from pathlib import Path

# Thresholds
MIN_TRADING_BALANCE = 50.0  # Minimum to start trading
OPTIMAL_TRADING_BALANCE = 200.0  # Target for full strategy

PRIVATE_ROOT = Path(os.getenv("HANDS_OFF_PRIVATE_DIR", str(Path.home() / ".config" / "hands-off-engine")))
STATE_FILE = PRIVATE_ROOT / "state" / "capital_recovery.json"
LOG_FILE = PRIVATE_ROOT / "logs" / "capital_recovery.log"


def get_balance():
    """Return a fresh verified wallet balance, or None when unknown."""
    try:
        import re
        from executor.trading_safeguards import TradingSafeguards
        safeguards = TradingSafeguards()
        ok, message = safeguards.check_wallet_balance(0)
        if not ok:
            return None
        match = re.search(r"balance:\s*\$([0-9]+(?:\.[0-9]+)?)", message, re.IGNORECASE)
        return float(match.group(1)) if match else None
    except Exception as exc:
        print(f"Balance verification unavailable: {type(exc).__name__}")
        return None

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
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

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


def trigger_singularity_if_ready(balance=None):
    """Compatibility stub: capital thresholds never authorize live trading."""
    log_event("LIVE_TRIGGER_BLOCKED: explicit governed approval required")
    return False

def check_recovery():
    """Read-only capital recovery monitor; never enables or starts live trading."""
    state = load_state()
    current_balance = get_balance()
    now = datetime.now(timezone.utc)
    events = []
    state["trading_enabled"] = False

    if current_balance is None:
        log_event("BALANCE_UNKNOWN: no authoritative wallet result; state unchanged")
        print(f"[{now.isoformat()}] Balance: UNKNOWN (unverified)")
        return {
            "balance": None,
            "balance_status": "unknown",
            "trading_enabled": False,
            "events": [],
        }

    previous_balance = state.get("last_balance") if state.get("last_balance_verified") else None
    print(
        f"[{now.isoformat()}] Verified balance: {current_balance:.2f} USD "
        + (f"(previous verified: {previous_balance:.2f} USD)" if previous_balance is not None else "(no prior verified baseline)")
    )

    if previous_balance is not None:
        balance_increase = current_balance - previous_balance
        if balance_increase > 10:
            event = {
                "type": "balance_increase",
                "timestamp": now.isoformat(),
                "previous": previous_balance,
                "current": current_balance,
                "increase": balance_increase,
            }
            events.append(event)
            state.setdefault("recovery_events", []).append(event)
            log_event(f"BALANCE_INCREASE: +{balance_increase:.2f} USD")

            if current_balance >= MIN_TRADING_BALANCE:
                if "capital_review" not in state.setdefault("alerts_sent", []):
                    send_telegram(
                        "Verified capital change detected. This monitor is read-only; "
                        "live trading remains disabled. Manual governed review is required.",
                        priority="high",
                    )
                    state["alerts_sent"].append("capital_review")

        if previous_balance >= MIN_TRADING_BALANCE and current_balance < MIN_TRADING_BALANCE:
            log_event(f"BALANCE_DROP: {previous_balance:.2f} -> {current_balance:.2f} USD")
            state["alerts_sent"] = []

    state["last_balance"] = current_balance
    state["last_balance_verified"] = True
    state["last_check"] = now.isoformat()
    state["trading_enabled"] = False
    save_state(state)

    return {
        "balance": current_balance,
        "balance_status": "verified",
        "trading_enabled": False,
        "events": events,
    }

def main():
    """Run a read-only recovery monitor."""
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    (PRIVATE_ROOT / "state").mkdir(parents=True, exist_ok=True, mode=0o700)
    (PRIVATE_ROOT / "logs").mkdir(parents=True, exist_ok=True, mode=0o700)
    env_file = PRIVATE_ROOT / ".env.polymarket"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("\"'")

    result = check_recovery()
    if result["balance_status"] == "verified":
        print(f"Balance: {result['balance']:.2f} USD")
    else:
        print("Balance: UNKNOWN (unverified)")
    print("Trading Enabled: False")
    print(f"Events: {len(result['events'])}")
    return result


if __name__ == "__main__":
    main()
