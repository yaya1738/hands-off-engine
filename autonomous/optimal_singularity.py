#!/usr/bin/env python3
"""Legacy singularity optimizer — disabled pending verified finances and authority."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> dict:
    """Report blocked status; never request deposits or initiate trades."""
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "blocked",
        "financial_balance": None,
        "positions": None,
        "execution_authorized": False,
        "reason": (
            "Historical market positions, capital gaps and wallet values in this "
            "legacy optimizer are not verified. Funding requests and live trading are disabled."
        ),
    }
    state_dir = Path(__file__).resolve().parent.parent / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "optimal_singularity_status.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )
    print("BLOCKED: no deposit request, Telegram message, or trade was initiated.")
    return result


if __name__ == "__main__":
    main()
