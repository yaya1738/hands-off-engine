#!/usr/bin/env python3
"""
Legacy cron installer — disabled.

Direct crontab mutation is intentionally blocked. The governed supervisor is
the only supported owner of runtime scheduling. --show is historical reference
only and does not imply that these jobs are installed or installable.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Cron job definitions
CRON_JOBS = [
    # Trading pipeline - run hourly at minute 0
    {
        "schedule": "0 * * * *",
        "command": f"cd {REPO_ROOT} && HANDS_OFF_EXECUTOR_MODE=shadow python3 scripts/run_pipeline.py >> /var/log/hands-off/pipeline.log 2>&1",
        "description": "Trading pipeline (hourly)"
    },
    # Health check - every 15 minutes
    {
        "schedule": "*/15 * * * *",
        "command": f"cd {REPO_ROOT} && ./scripts/healthcheck.sh >> /var/log/hands-off/health.log 2>&1",
        "description": "Health monitoring (15 min)"
    },
    # Phase progression - daily at midnight UTC
    {
        "schedule": "0 0 * * *",
        "command": f"cd {REPO_ROOT} && python3 scripts/autonomous_phase_manager.py >> /var/log/hands-off/phase.log 2>&1",
        "description": "Phase progression (daily)"
    },
    # Coordination agent - every 5 minutes
    {
        "schedule": "*/5 * * * *",
        "command": f"cd {REPO_ROOT} && python3 scripts/coordination_agent.py --once >> /var/log/hands-off/coordination.log 2>&1",
        "description": "Coordination agent (5 min)"
    },
    # Claude orchestrator - every 30 minutes
    {
        "schedule": "*/30 * * * *",
        "command": f"cd {REPO_ROOT} && python3 scripts/claude_orchestrator.py >> /var/log/hands-off/orchestrator.log 2>&1",
        "description": "Claude orchestrator (30 min)"
    },
    # Self-improvement kernel refresh - every 6 hours
    {
        "schedule": "0 */6 * * *",
        "command": f"cd {REPO_ROOT} && python3 -c \"from ai_nexus.spark_plug_autokernel import refresh_all_kernels; refresh_all_kernels()\" >> /var/log/hands-off/self-improve.log 2>&1",
        "description": "Self-improvement cycle (6 hours)"
    },
    # Revenue tracking - every 4 hours
    {
        "schedule": "0 */4 * * *",
        "command": f"cd {REPO_ROOT} && python3 revenue/master_revenue_engine.py >> /var/log/hands-off/revenue.log 2>&1",
        "description": "Revenue tracking (4 hours)"
    },
    # Performance metrics - every hour at minute 30
    {
        "schedule": "30 * * * *",
        "command": f"cd {REPO_ROOT} && python3 scripts/track_performance.py >> /var/log/hands-off/metrics.log 2>&1",
        "description": "Performance metrics (hourly)"
    },
]

CRON_MARKER = "# HANDS-OFF-ENGINE AUTONOMOUS CRON"


def get_current_crontab() -> str:
    """Get current crontab content"""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def install_cron_jobs():
    """Legacy cron installation is disabled; use the governed supervisor."""
    print("BLOCKED: direct crontab installation is disabled.")
    return False

def remove_cron_jobs():
    """Legacy crontab removal is disabled to avoid mutating unrelated jobs."""
    print("BLOCKED: direct crontab mutation is disabled.")
    return False

def show_cron_jobs():
    """Show what would be installed"""
    print("BLOCKED: legacy cron definitions are reference-only and will not be installed.")
    print("The governed supervisor owns runtime scheduling.")
    print("=" * 60)
    print()

    for job in CRON_JOBS:
        print(f"{job['description']}")
        print(f"  Schedule: {job['schedule']}")
        print(f"  Command:  {job['command'][:80]}...")
        print()

    print("=" * 60)
    print(f"Historical definitions: {len(CRON_JOBS)} (installation disabled)")


def main():
    parser = argparse.ArgumentParser(description="Manage autonomous operation cron jobs")
    parser.add_argument("--install", action="store_true", help="Install cron jobs")
    parser.add_argument("--remove", action="store_true", help="Remove cron jobs")
    parser.add_argument("--show", action="store_true", help="Show what would be installed")

    args = parser.parse_args()

    if args.install:
        success = install_cron_jobs()
        sys.exit(0 if success else 1)
    elif args.remove:
        success = remove_cron_jobs()
        sys.exit(0 if success else 1)
    elif args.show:
        show_cron_jobs()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
