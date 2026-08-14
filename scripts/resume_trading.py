#!/usr/bin/env python3
"""Fail-closed manual financial activation entry point.

This legacy command is intentionally unable to enable live trading by itself.
A human must complete the current-rules/financial approval process through the
authoritative Factory authority path. This prevents a convenience script from
becoming a second trading authority.
"""

from __future__ import annotations

import logging

from executor.trading_safeguards import load_mode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOG = logging.getLogger(__name__)


def main() -> int:
    mode = load_mode()
    if mode.get("live_trading_enabled", False):
        LOG.info("Trading is already enabled; this legacy entry point makes no changes.")
        return 0

    LOG.error("FAIL-CLOSED: this legacy resume command cannot enable live trading.")
    LOG.error(
        "Live financial activation requires the authoritative Factory authority "
        "path, a fresh current-rules check, and explicit human approval."
    )
    LOG.error("No trading state was modified.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
