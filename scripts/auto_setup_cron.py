#!/usr/bin/env python3
"""
Auto Setup Cron - Install all autonomous operation cron jobs

This script installs the cron jobs needed for fully autonomous operation:
- Trading pipeline (hourly)
- Health monitoring (every 15 min)
- Phase progression (daily)
- Coordination agent (every 5 min)
- Claude orchestrator (every 30 min)
- Self-improvement cycle (every 6 hours)

Usage:
    python3 auto_setup_cron.py --install   # Install cron jobs
    python3 auto_setup_cron.py --remove    # Remove cron jobs
    python3 auto_setup_cron.py --show      # Show what would be installed
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
    """Install all cron jobs"""
    print("Installing autonomous operation cron jobs...")
    print()

    # Get existing crontab (without our jobs)
    existing = get_current_crontab()

    # Remove any existing hands-off cron jobs
    lines = existing.split('\n')
    cleaned_lines = []
    skip_next = False

    for line in lines:
        if CRON_MARKER in line:
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue
        if line.strip():
            cleaned_lines.append(line)

    # Build new crontab
    new_crontab_lines = cleaned_lines + ["", CRON_MARKER]

    for job in CRON_JOBS:
        comment = f"# {job['description']}"
        cron_line = f"{job['schedule']} {job['command']}"
        new_crontab_lines.extend([comment, cron_line])

    new_crontab = '\n'.join(new_crontab_lines) + '\n'

    # Install new crontab
    try:
        process = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            text=True
        )
        process.communicate(input=new_crontab)

        if process.returncode == 0:
            print(f"Installed {len(CRON_JOBS)} cron jobs:")
            for job in CRON_JOBS:
                print(f"  - {job['description']}")
            print()
            print("Cron jobs are now active!")
            return True
        else:
            print("ERROR: Failed to install crontab")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def remove_cron_jobs():
    """Remove all hands-off cron jobs"""
    print("Removing hands-off cron jobs...")

    existing = get_current_crontab()

    # Remove our jobs
    lines = existing.split('\n')
    cleaned_lines = []
    skip_next = False

    for line in lines:
        if CRON_MARKER in line:
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue
        if line.strip():
            cleaned_lines.append(line)

    new_crontab = '\n'.join(cleaned_lines) + '\n' if cleaned_lines else ""

    try:
        if new_crontab.strip():
            process = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=new_crontab)
        else:
            subprocess.run(["crontab", "-r"], capture_output=True)

        print("Hands-off cron jobs removed")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def show_cron_jobs():
    """Show what would be installed"""
    print("Cron jobs that will be installed:")
    print("=" * 60)
    print()

    for job in CRON_JOBS:
        print(f"{job['description']}")
        print(f"  Schedule: {job['schedule']}")
        print(f"  Command:  {job['command'][:80]}...")
        print()

    print("=" * 60)
    print(f"Total: {len(CRON_JOBS)} cron jobs")


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
