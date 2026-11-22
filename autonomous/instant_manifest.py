#!/usr/bin/env python3
"""Legacy instant-manifest workflow — observation only, no financial activation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def manifest_compound_multiplier() -> dict:
    return {
        "status": "blocked",
        "balance": None,
        "positions": None,
        "execution_authorized": False,
    }


def manifest_signal_readiness() -> dict:
    return {
        "status": "research_only",
        "execution_authorized": False,
        "reason": "No governed live execution grant is available",
    }


def manifest_resolution_countdown() -> dict:
    return {
        "status": "stale_historical_data",
        "execution_authorized": False,
        "reason": "No current position-resolution feed is connected",
    }


def manifest_escape_velocity_score() -> dict:
    return {
        "status": "unverified",
        "capital": None,
        "trading": "disabled",
        "income": None,
        "score": None,
    }


def manifest_complete_state() -> dict:
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "financial": {
            "balance_usd": None,
            "positions_usd": None,
            "net_liquid_assets": None,
            "status": "unverified",
            "trading_enabled": False,
        },
        "readiness": {
            "signals_prepared": None,
            "execution_authorized": False,
        },
    }
    state_file = Path(__file__).resolve().parent.parent / "state" / "MANIFESTED_STATE.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def main() -> dict:
    result = {
        "financial": manifest_compound_multiplier(),
        "signals": manifest_signal_readiness(),
        "positions": manifest_resolution_countdown(),
        "escape_velocity": manifest_escape_velocity_score(),
        "state": manifest_complete_state(),
    }
    print("Instant manifest is observation-only; no financial or external actions were taken.")
    return result


if __name__ == "__main__":
    main()
