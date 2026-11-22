#!/usr/bin/env python3
"""Legacy time-collapse runner — evidence-only, no financial execution."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "state" / "time_collapse.json"
LOG_FILE = BASE_DIR / "state" / "logs" / "time_collapse.log"

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("time-collapse")


def log(message: str) -> None:
    LOG.info(message)


def send_telegram(message: str) -> bool:
    """Notifications are opt-in and require environment credentials."""
    import os
    import requests

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception:
        return False


def accelerate_capital_awareness() -> dict:
    """Report only a verified wallet balance; positions remain unknown."""
    balance = None
    verified = False
    try:
        from executor.trading_safeguards import TradingSafeguards
        ok, message = TradingSafeguards().check_wallet_balance(0)
        if ok and "balance: $" in message:
            balance = float(message.split("balance: $", 1)[1].split()[0])
            verified = True
    except Exception:
        pass
    return {
        "vector": "capital_awareness",
        "wallet_balance": balance,
        "wallet_verified": verified,
        "positions": None,
        "positions_verified": False,
        "execution_authorized": False,
    }


def accelerate_income_channels() -> dict:
    """Websites and signal files are not evidence of earned income."""
    return {
        "vector": "income_validation",
        "verified_income_channels": 0,
        "revenue": None,
        "status": "unverified",
    }


def accelerate_automation() -> dict:
    return {"vector": "automation", "status": "observation_only"}


def accelerate_intelligence() -> dict:
    return {"vector": "intelligence", "status": "observation_only"}


def accelerate_momentum() -> dict:
    return {"vector": "momentum", "status": "unverified"}


def define_completed_state() -> dict:
    return {
        "balance_usd": None,
        "income_streams": None,
        "escape_velocity_score": None,
        "status": "targets_require_verified_financial_inputs",
    }


def calculate_gap(current: dict, target: dict) -> dict:
    return {
        "balance_gap": None,
        "income_gap": None,
        "velocity_gap": None,
        "status": "not_calculable_without_verified_inputs",
    }


def collapse_timeline() -> dict:
    """Collect bounded observations; never run commands or change financial state."""
    results = {
        "capital": accelerate_capital_awareness(),
        "income": accelerate_income_channels(),
        "automation": accelerate_automation(),
        "intelligence": accelerate_intelligence(),
        "momentum": accelerate_momentum(),
    }
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "observation_only",
        "execution_authorized": False,
        "current_state": {
            "balance": results["capital"]["wallet_balance"],
            "balance_verified": results["capital"]["wallet_verified"],
            "positions": None,
            "income_channels": 0,
            "income_verified": False,
        },
        "target_state": define_completed_state(),
        "gaps": calculate_gap({}, {}),
        "vector_results": results,
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    log("Time-collapse legacy runner completed observation only; no actions executed.")
    return state


def execute_immediate_actions() -> dict:
    """Legacy action runner is disabled; return recommendations without executing."""
    return {
        "status": "blocked",
        "execution_authorized": False,
        "actions_executed": 0,
        "reason": "No governed execution grant is integrated",
    }


if __name__ == "__main__":
    collapse_timeline()
