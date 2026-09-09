"""Compatibility CLI for the integrated autonomous runtime.

The production entrypoint now runs the existing infrastructure loop together
with the Factory learning/improvement loop.
"""
from __future__ import annotations

import argparse

from .integrated_runtime import start_live_system


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the integrated autonomous system")
    parser.add_argument("--budget", type=float, default=500.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    start_live_system(budget=args.budget, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
