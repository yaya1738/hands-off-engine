#!/usr/bin/env python3
"""
Self-Healing Agent Runner

Runs the watchdog which monitors and heals the system continuously.
Can be run as a standalone service or from cron.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.watchdog import Watchdog


def main():
    parser = argparse.ArgumentParser(description='Run self-healing agent system')
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300 = 5 minutes)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (useful for cron)'
    )
    
    args = parser.parse_args()
    
    watchdog = Watchdog()
    
    if args.once:
        # Run single cycle
        import json
        results = watchdog.run_watch_cycle()
        print(json.dumps(results, indent=2))
    else:
        # Run forever
        watchdog.run_forever(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
