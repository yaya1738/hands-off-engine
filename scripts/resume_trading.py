#!/usr/bin/env python3
"""Legacy manual resume command — disabled pending governed execution authority."""

import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


def main():
    """Do not mutate live-trading state from this legacy command."""
    LOG.warning(
        "Trading resume blocked: this command cannot grant execution authority. "
        "Use the governed approval workflow after financial-integrity review."
    )
    print("BLOCKED: live trading remains disabled; no state was changed.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
