#!/usr/bin/env python3
"""
SINGULARITY TRIGGER
===================

The moment capital crosses the trading threshold ($50),
this trigger fires and executes EVERYTHING instantly:

1. Enable live trading
2. Execute prepared signals
3. Maximize escape velocity
4. Notify of breakthrough

This is the inflection point where all preparation
collapses into instant execution.
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

TRIGGER_STATE = BASE_DIR / "state" / "singularity_trigger.json"
TRADING_THRESHOLD = 50.0
MINIMUM_VIABLE_THRESHOLD = 25.0  # Can do small trades at $25


def log(msg: str):
    print(f"💥 {msg}")


def send_telegram(msg: str, priority: str = "normal"):
    """Send notifications only when credentials are supplied through the environment."""
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    if priority == "critical":
        msg = "🚨🚨🚨\n" + msg
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception:
        return False


def get_balance() -> float | None:
    """Return a balance only when both supported token balances are verified."""
    try:
        from executor.trading_safeguards import TradingSafeguards
        ok, msg = TradingSafeguards().check_wallet_balance(0)
        if not ok:
            return None
        if "balance: $" in msg:
            return float(msg.split("balance: $", 1)[1].split()[0])
    except Exception:
        return None
    return None


def load_state() -> dict:
    if TRIGGER_STATE.exists():
        return json.load(open(TRIGGER_STATE))
    return {
        "triggered": False,
        "trigger_time": None,
        "trigger_balance": None,
        "actions_executed": [],
        "escape_velocity_at_trigger": None
    }


def save_state(state: dict):
    with open(TRIGGER_STATE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def execute_singularity():
    """Legacy execution entry point is permanently fail-closed."""
    return [{
        "status": "blocked",
        "execution_authorized": False,
        "reason": "Threshold monitoring cannot authorize trading or system mutations",
    }]


def execute_mini_singularity(balance: float):
    """Legacy mini-execution entry point is permanently fail-closed."""
    return [{
        "status": "blocked",
        "execution_authorized": False,
        "reason": "Threshold monitoring cannot authorize trading or system mutations",
    }]


def check_and_trigger():
    """Observe verified wallet thresholds; never execute or enable trading."""
    state = load_state()
    balance = get_balance()
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    state["trading_enabled"] = False
    state["execution_authorized"] = False

    if balance is None:
        state["financial_status"] = "unknown"
        state["last_balance"] = None
        state["approval_required"] = False
        state["message"] = "Wallet balance could not be verified; no action taken."
        save_state(state)
        log(state["message"])
        return state

    state["financial_status"] = "verified_read_only"
    state["last_balance"] = balance
    if balance >= TRADING_THRESHOLD:
        state["threshold_status"] = "full_threshold_observed"
        state["approval_required"] = True
        state["message"] = (
            "Capital threshold observed. No trading or financial action executed; "
            "explicit governed approval is required."
        )
        send_telegram(
            f"Capital threshold observed: ${balance:.2f}. No trades were executed. "
            "Explicit approval is required.",
            priority="critical",
        )
    elif balance >= MINIMUM_VIABLE_THRESHOLD:
        state["threshold_status"] = "minimum_threshold_observed"
        state["approval_required"] = True
        state["message"] = (
            "Minimum capital threshold observed. No trading or financial action executed; "
            "explicit governed approval is required."
        )
        send_telegram(
            f"Minimum capital threshold observed: ${balance:.2f}. No trades were executed.",
            priority="normal",
        )
    else:
        state["threshold_status"] = "below_threshold"
        state["approval_required"] = False
        state["message"] = "Below threshold; observation only."

    state["legacy_triggered_flag_ignored"] = bool(state.get("triggered"))
    save_state(state)
    log(state["message"])
    return state


def main():
    """Main entry point"""

    # Load env
    env_file = BASE_DIR / ".env.polymarket"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

    log("SINGULARITY TRIGGER - Monitoring for breakthrough...")
    log("")

    state = check_and_trigger()

    log("Observation-only mode. Capital thresholds never trigger automatic execution.")


if __name__ == "__main__":
    main()
