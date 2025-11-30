#!/usr/bin/env python3
"""
Auto-Setup Cron Jobs - Autonomous Scheduling Configuration
============================================================

This script automatically configures all necessary cron jobs for the
hands-off-engine to run autonomously without manual crontab editing.

Jobs configured:
1. Main trading pipeline (hourly)
2. Social media promotion (every 4 hours)
3. Health check monitoring (every 15 minutes)
4. Daily recalibration (08:00 UTC)
5. Performance reporting (daily)
6. Coordination agent (every 5 minutes)

Usage:
    python3 scripts/auto_setup_cron.py --install    # Install all crons
    python3 scripts/auto_setup_cron.py --remove     # Remove all crons
    python3 scripts/auto_setup_cron.py --status     # Show current status
"""

import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
VENV_PYTHON = "/usr/bin/python3"  # Use system Python or venv if available

# Define all cron jobs with schedule and command
CRON_JOBS = {
    "trading_pipeline": {
        "schedule": "0 * * * *",  # Every hour at :00
        "command": f"cd {REPO_ROOT} && HANDS_OFF_EXECUTOR_MODE=shadow ./scripts/run_and_notify.sh >> /var/log/hands-off/trading.log 2>&1",
        "description": "Main trading pipeline (shadow mode)"
    },
    "social_promotion": {
        "schedule": "0 */4 * * *",  # Every 4 hours
        "command": f"cd {REPO_ROOT} && {VENV_PYTHON} api/social_promotion.py >> /var/log/hands-off/social.log 2>&1",
        "description": "Social media promotion cycle"
    },
    "health_check": {
        "schedule": "*/15 * * * *",  # Every 15 minutes
        "command": f"cd {REPO_ROOT} && ./scripts/healthcheck.sh >> /var/log/hands-off/health.log 2>&1",
        "description": "System health monitoring"
    },
    "daily_recalibration": {
        "schedule": "0 8 * * *",  # Daily at 08:00 UTC
        "command": f"cd {REPO_ROOT} && {VENV_PYTHON} scripts/recalibrate_engine.py >> /var/log/hands-off/recalibrate.log 2>&1",
        "description": "Daily model recalibration"
    },
    "performance_report": {
        "schedule": "0 20 * * *",  # Daily at 20:00 UTC
        "command": f"cd {REPO_ROOT} && {VENV_PYTHON} scripts/track_performance.py --notify >> /var/log/hands-off/performance.log 2>&1",
        "description": "Daily performance report"
    },
    "coordination_agent": {
        "schedule": "*/5 * * * *",  # Every 5 minutes
        "command": f"cd {REPO_ROOT} && {VENV_PYTHON} scripts/coordination_agent.py --once >> /var/log/hands-off/coordination.log 2>&1",
        "description": "AI coordination agent"
    },
    "phase_progression": {
        "schedule": "0 0 * * *",  # Daily at midnight
        "command": f"cd {REPO_ROOT} && {VENV_PYTHON} scripts/autonomous_phase_manager.py >> /var/log/hands-off/phases.log 2>&1",
        "description": "Auto phase progression check"
    }
}

# Marker to identify our cron entries
CRON_MARKER = "# HANDS-OFF-ENGINE AUTO-MANAGED"


def get_current_crontab() -> str:
    """Get current crontab contents."""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def set_crontab(content: str) -> bool:
    """Set new crontab contents."""
    try:
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=content)
        return process.returncode == 0
    except Exception as e:
        print(f"Error setting crontab: {e}")
        return False


def ensure_log_directory():
    """Create log directory if it doesn't exist."""
    log_dir = Path("/var/log/hands-off")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Log directory ready: {log_dir}")
    except PermissionError:
        # Try with sudo
        subprocess.run(['sudo', 'mkdir', '-p', str(log_dir)], check=True)
        subprocess.run(['sudo', 'chmod', '777', str(log_dir)], check=True)
        print(f"✓ Log directory created (with sudo): {log_dir}")


def install_cron_jobs():
    """Install all autonomous cron jobs."""
    print("=" * 60)
    print("HANDS-OFF-ENGINE: Auto-Installing Cron Jobs")
    print("=" * 60)

    # Ensure log directory exists
    ensure_log_directory()

    # Get current crontab
    current = get_current_crontab()

    # Remove any existing hands-off entries
    lines = [line for line in current.split('\n')
             if CRON_MARKER not in line and 'hands-off-engine' not in line.lower()]

    # Add new entries
    new_entries = ["\n", f"{CRON_MARKER} - DO NOT EDIT BELOW THIS LINE"]
    new_entries.append(f"# Installed: {datetime.utcnow().isoformat()}Z")
    new_entries.append("")

    for job_id, job in CRON_JOBS.items():
        new_entries.append(f"# {job['description']}")
        new_entries.append(f"{job['schedule']} {job['command']} {CRON_MARKER}")
        new_entries.append("")

    new_entries.append(f"# END {CRON_MARKER}")

    # Combine and set
    new_crontab = '\n'.join(lines) + '\n'.join(new_entries)

    if set_crontab(new_crontab):
        print("\n✓ All cron jobs installed successfully!\n")
        print("Installed jobs:")
        for job_id, job in CRON_JOBS.items():
            print(f"  • {job_id}: {job['schedule']} - {job['description']}")
        print("\n" + "=" * 60)
        return True
    else:
        print("\n✗ Failed to install cron jobs")
        return False


def remove_cron_jobs():
    """Remove all hands-off cron jobs."""
    print("Removing HANDS-OFF-ENGINE cron jobs...")

    current = get_current_crontab()

    # Remove all hands-off entries
    lines = [line for line in current.split('\n')
             if CRON_MARKER not in line and 'hands-off-engine' not in line.lower()]

    # Clean up empty lines at end
    while lines and not lines[-1].strip():
        lines.pop()

    if set_crontab('\n'.join(lines) + '\n'):
        print("✓ All HANDS-OFF-ENGINE cron jobs removed")
        return True
    else:
        print("✗ Failed to remove cron jobs")
        return False


def show_status():
    """Show current cron job status."""
    print("=" * 60)
    print("HANDS-OFF-ENGINE: Cron Job Status")
    print("=" * 60)

    current = get_current_crontab()

    # Find our jobs
    our_jobs = [line for line in current.split('\n')
                if CRON_MARKER in line or 'hands-off-engine' in line.lower()]

    if our_jobs:
        print("\n✓ Found installed cron jobs:\n")
        for line in our_jobs:
            if line.strip() and not line.startswith('#'):
                # Parse schedule from line
                parts = line.split()
                if len(parts) >= 5:
                    schedule = ' '.join(parts[:5])
                    print(f"  Schedule: {schedule}")
    else:
        print("\n⚠ No HANDS-OFF-ENGINE cron jobs found")
        print("  Run: python3 scripts/auto_setup_cron.py --install")

    print("\n" + "=" * 60)

    # Also show log file status
    log_dir = Path("/var/log/hands-off")
    if log_dir.exists():
        print("\nLog files:")
        for log_file in log_dir.glob("*.log"):
            size = log_file.stat().st_size
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"  • {log_file.name}: {size} bytes, last modified {mtime}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1].lower()

    if action in ['--install', '-i', 'install']:
        success = install_cron_jobs()
        sys.exit(0 if success else 1)

    elif action in ['--remove', '-r', 'remove', '--uninstall']:
        success = remove_cron_jobs()
        sys.exit(0 if success else 1)

    elif action in ['--status', '-s', 'status']:
        show_status()
        sys.exit(0)

    else:
        print(f"Unknown action: {action}")
        print("Use --install, --remove, or --status")
        sys.exit(1)


if __name__ == '__main__':
    main()
