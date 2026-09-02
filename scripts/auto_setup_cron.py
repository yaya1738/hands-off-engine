#!/usr/bin/env python3
"""Legacy cron setup compatibility facade.

Direct installation/removal of autonomous cron jobs is retired. Runtime
scheduling must be owned by the Factory authority; this module is informational
only and cannot mutate the host crontab.
"""

import argparse

CRON_MARKER = "# HANDS-OFF-ENGINE AUTONOMOUS CRON"
CRON_JOBS = [
    {"schedule": "0 * * * *", "description": "Trading pipeline (hourly)"},
    {"schedule": "*/15 * * * *", "description": "Health monitoring (15 min)"},
    {"schedule": "0 0 * * *", "description": "Phase progression (daily)"},
    {"schedule": "*/5 * * * *", "description": "Coordination agent (5 min)"},
    {"schedule": "*/30 * * * *", "description": "Claude orchestrator (30 min)"},
    {"schedule": "0 */6 * * *", "description": "Self-improvement cycle (6 hours)"},
    {"schedule": "0 */4 * * *", "description": "Revenue tracking (4 hours)"},
    {"schedule": "30 * * * *", "description": "Performance metrics (hourly)"},
]


def get_current_crontab() -> str:
    """Read-only compatibility result; host cron is outside this module's authority."""
    return ""


def install_cron_jobs() -> bool:
    print("[FACTORY-AUTHORITY] Legacy cron installation is disabled; scheduling must be configured by the authoritative runtime.")
    return False


def remove_cron_jobs() -> bool:
    print("[FACTORY-AUTHORITY] Legacy cron removal is disabled; host scheduling cannot be mutated by this compatibility path.")
    return False


def show_cron_jobs():
    print("Factory-authorized scheduling objectives (informational only):")
    print("=" * 60)
    for job in CRON_JOBS:
        print(f"{job['description']}: {job['schedule']}")
    print("=" * 60)
    print("No host crontab changes are performed by this module.")


def main():
    parser = argparse.ArgumentParser(description="Informational autonomous scheduling compatibility tool")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    if args.install:
        raise SystemExit(0 if install_cron_jobs() else 1)
    if args.remove:
        raise SystemExit(0 if remove_cron_jobs() else 1)
    show_cron_jobs() if args.show else parser.print_help()


if __name__ == "__main__": main()
