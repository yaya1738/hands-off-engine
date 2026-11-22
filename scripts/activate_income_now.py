#!/usr/bin/env python3
"""Legacy income activation entry point — blocked pending verified financial truth."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    """Do not send funding requests, publish promotions, or initiate trading."""
    state_dir = REPO_ROOT / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "blocked",
        "external_actions": False,
        "trading_enabled": False,
        "reason": (
            "Legacy activation script contains stale financial assumptions. "
            "Earned-income offers require current evidence and explicit publication approval."
        ),
    }
    log_file = state_dir / "income_activation_log.jsonl"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    print("BLOCKED: no funding request, trade, promotion or external message was sent.")
    print(record["reason"])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
