#!/usr/bin/env python3
"""Shadow-only financial recalibration entry point.

This legacy entry point is intentionally non-authoritative. It may inspect and
recalibrate paper/shadow risk state, but it MUST NOT enable live trading.

Live financial execution requires the separate global trading ban, current
market-rules gate, and explicit human approval. No autonomous recalibration
may switch that lane on.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from executor.trading_safeguards import load_mode

LOG = logging.getLogger("recalibrate_engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main() -> int:
    mode = load_mode()
    if mode.get("live_trading_enabled", False):
        LOG.error("FAIL-CLOSED: live trading state is enabled; recalibration will not modify it.")
        LOG.error("A human rules gate must explicitly authorize any financial activation.")
        return 2

    LOG.info("Shadow recalibration only: live trading remains disabled.")
    LOG.info("Mode reason=%s", mode.get("reason", "unknown"))
    LOG.info("Timestamp=%s", datetime.now(timezone.utc).isoformat())
    LOG.info("No live-trading resume or activation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
