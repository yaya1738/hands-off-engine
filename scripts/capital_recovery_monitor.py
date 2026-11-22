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

# Thresholds
MIN_TRADING_BALANCE = 50.0  # Minimum to start trading
OPTIMAL_TRADING_BALANCE = 200.0  # Target for full strategy

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "state" / "capital_recovery.json"
LOG_FILE = BASE_DIR / "state" / "logs" / "capital_recovery.log"


def get_balance() -> float | None:
    """Return only a balance verified by both supported USDC token queries."""
    try:
        from executor.trading_safeguards import TradingSafeguards
        ok, message = TradingSafeguards().check_wallet_balance(0)
        if not ok or "balance: $" not in message:
            return None
        return float(message.split("balance: $", 1)[1].split()[0])
    except Exception as exc:
        print(f"Balance verification unavailable: {exc}")
        return None


def load_state() -> dict:
    """Load previous state"""
    if STATE_FILE.exists():
        return json.load(open(STATE_FILE))
    return {
        "last_balance": None,
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
    """Send notifications only when credentials are explicitly configured."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    if priority == "high":
        message = "🚨🚨🚨\n" + message
    elif priority == "medium":
        message = "⚡\n" + message

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        print(f"Telegram notification failed: {exc}")
        return False


def log_event(event: str):
    """Log to file"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {event}\n")


def trigger_singularity_if_ready(balance: float):
    """Legacy trigger is disabled; a balance threshold is never execution authority."""
    return {
        "status": "blocked",
        "execution_authorized": False,
        "reason": "Capital recovery monitoring is observation-only",
    }


def check_recovery():
    """Record verified balance observations without enabling or executing trading."""
    state = load_state()
    current_balance = get_balance()
    now = datetime.now(timezone.utc)
    state["last_check"] = now.isoformat()
    state["trading_enabled"] = False
    state["execution_authorized"] = False

    if current_balance is None:
        state["financial_status"] = "unknown"
        state["last_balance"] = None
        state["approval_required"] = False
        save_state(state)
        return {
            "balance": None,
            "financial_status": "unknown",
            "trading_enabled": False,
            "execution_authorized": False,
            "events": [],
        }

    previous_balance = state.get("last_balance")
    state["financial_status"] = "verified_read_only"
    events = []

    if isinstance(previous_balance, (int, float)):
        change = current_balance - float(previous_balance)
        if abs(change) > 10:
            event = {
                "type": "balance_change_observed",
                "timestamp": now.isoformat(),
                "previous": float(previous_balance),
                "current": current_balance,
                "change": change,
                "position_resolution_verified": False,
            }
            events.append(event)
            state.setdefault("recovery_events", []).append(event)
            log_event(
                f"BALANCE_CHANGE_OBSERVED: {change:+.2f}; source attribution unverified"
            )

    state["last_balance"] = current_balance
    state["threshold_status"] = (
        "capital_threshold_observed"
        if current_balance >= MIN_TRADING_BALANCE
        else "below_threshold"
    )
    state["approval_required"] = current_balance >= MIN_TRADING_BALANCE

    if current_balance >= MIN_TRADING_BALANCE:
        send_telegram(
            f"Verified wallet balance observed: ${current_balance:.2f}. "
            "No trading action was taken; governed approval is required.",
            priority="medium",
        )

    save_state(state)
    return {
        "balance": current_balance,
        "financial_status": "verified_read_only",
        "trading_enabled": False,
        "execution_authorized": False,
        "approval_required": state["approval_required"],
        "events": events,
    }


def main():
    """Run recovery monitor"""
    # Load env
    env_file = BASE_DIR / ".env.polymarket"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

    result = check_recovery()

    print(f"\nCapital Recovery Status:")
    balance = result["balance"]
    print("  Balance: UNKNOWN" if balance is None else f"  Balance: ${balance:.2f}")
    print("  Trading Enabled: False (observation-only)")
    print(f"  Events: {len(result['events'])}")

    return result


if __name__ == "__main__":
    main()
