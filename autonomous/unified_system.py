"""Compatibility CLI for the unified autonomous runtime.

The implementation lives in :mod:`autonomous.orchestrator`; this module
preserves the production service entrypoint ``python -m autonomous.unified_system``.
"""

from __future__ import annotations

import argparse

from .orchestrator import start_live_system


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the unified autonomous system")
    parser.add_argument("--budget", type=float, default=500.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    start_live_system(budget=args.budget, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
