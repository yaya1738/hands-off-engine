#!/usr/bin/env python3
"""Legacy cash-generation planner — research only, no bankroll assumptions or execution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
SIGNALS_FILE = BASE_DIR / "state" / "crypto_focused_signals.json"


def load_signals() -> list[dict[str, Any]]:
    """Load research signals without treating them as executable orders."""
    try:
        data = json.loads(SIGNALS_FILE.read_text())
        markets = data.get("markets", [])
        return sorted(
            [item for item in markets if isinstance(item, dict)],
            key=lambda item: float(item.get("model_edge", 0) or 0),
            reverse=True,
        )
    except (OSError, ValueError, TypeError):
        return []


def generate_execution_plan() -> dict[str, Any]:
    """Fail closed: no cached bankroll, sizing, or execution plan is authoritative."""
    signals = load_signals()
    return {
        "status": "blocked",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "signals_observed": len(signals),
        "bankroll": None,
        "trades": [],
        "execution_authorized": False,
        "reason": (
            "Legacy planner disabled: verified wallet balance, calibrated edge, "
            "risk approval, and governed execution are not integrated."
        ),
    }


def print_status() -> dict[str, Any]:
    result = generate_execution_plan()
    print("CASH-GENERATION PLANNER: BLOCKED")
    print(f"Research signals observed: {result['signals_observed']}")
    print("Verified spendable balance: UNKNOWN")
    print("Order sizing: DISABLED")
    print("Live execution: DISABLED")
    print(result["reason"])
    return result


if __name__ == "__main__":
    print_status()
