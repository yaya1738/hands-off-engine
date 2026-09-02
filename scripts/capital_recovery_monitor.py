#!/usr/bin/env python3
"""Read-only compatibility facade for the legacy capital recovery monitor.

Capital recovery detection may be observed, but trading, notification, and
state mutation require FactoryAuthorityGateway. Legacy autonomous execution
is intentionally fail-closed here.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "state" / "capital_recovery.json"
LOG_FILE = BASE_DIR / "state" / "capital_recovery.log"
MIN_TRADING_BALANCE = 50.0
OPTIMAL_TRADING_BALANCE = 200.0


def log_event(event: str) -> bool:
    """Record only local diagnostic information; never grants execution authority."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {event}\n")
        return True
    except OSError:
        return False


def get_balance() -> float:
    """Return no balance data through this legacy execution surface."""
    return 0.0


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return {
        "last_balance": 0.0,
        "last_check": None,
        "recovery_events": [],
        "trading_enabled": False,
        "alerts_sent": [],
        "authority_required": True,
        "disabled": True,
    }


def save_state(state: dict) -> bool:
    log_event("[FACTORY-AUTHORITY] state mutation is disabled; submit through FactoryAuthorityGateway")
    return False


def send_telegram(message: str, priority: str = "normal") -> bool:
    log_event("[FACTORY-AUTHORITY] notification delivery is disabled")
    return False


def trigger_singularity_if_ready(balance: float):
    log_event("[FACTORY-AUTHORITY] singularity execution is disabled; submit through FactoryAuthorityGateway")
    return ["[FACTORY-AUTHORITY] authority_required"]


def check_recovery() -> dict:
    state = load_state()
    now = datetime.now(timezone.utc).isoformat()
    state["last_check"] = now
    state["authority_required"] = True
    state["disabled"] = True
    state["trading_enabled"] = False
    return {
        "balance": 0.0,
        "trading_enabled": False,
        "events": [],
        "authority_required": True,
        "disabled": True,
    }


def main():
    result = check_recovery()
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
