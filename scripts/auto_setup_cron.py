#!/usr/bin/env python3
"""
Auto Setup Cron - Configure all autonomous system cron jobs

Installs cron jobs for:
- Trading pipeline
- Social promotion
- Health monitoring
- Phase progression
- Coordination agent
- Self-healing agent
- Hardware management
- Infrastructure scaling
"""

import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# All cron jobs for the autonomous system
CRON_JOBS = [
    # Trading & Revenue
    {
        "schedule": "0 * * * *",
        "command": f"cd {REPO_ROOT} && ./scripts/run_and_notify.sh",
        "description": "Trading pipeline - hourly"
    },
    {
        "schedule": "0 */4 * * *",
        "command": f"cd {REPO_ROOT} && python3 api/social_promotion.py",
        "description": "Social promotion - every 4 hours"
    },

    # Monitoring & Health
    {
        "schedule": "*/15 * * * *",
        "command": f"python3 {REPO_ROOT}/scripts/healthcheck.py",
        "description": "Health monitoring - every 15 minutes"
    },
    {
        "schedule": "*/5 * * * *",
        "command": f"python3 {REPO_ROOT}/scripts/coordination_agent.py --once",
        "description": "Coordination agent - every 5 minutes"
    },

    # Self-Healing & Hardware Management
    {
        "schedule": "*/5 * * * *",
        "command": f"python3 {REPO_ROOT}/scripts/self_healing_agent.py --once",
        "description": "Self-healing agent - every 5 minutes"
    },
    {
        "schedule": "*/15 * * * *",
        "command": f"python3 {REPO_ROOT}/scripts/hardware_management_cron.py",
        "description": "Hardware management - every 15 minutes"
    },
    {
        "schedule": "0 * * * *",
        "command": f"cd {REPO_ROOT} && python3 -m infrastructure.autonomous_infra_manager",
        "description": "Infrastructure manager - hourly"
    },

    # Daily Tasks
    {
        "schedule": "0 8 * * *",
        "command": f"python3 {REPO_ROOT}/alpha/intelligent_alpha_engine.py recalibrate",
        "description": "Daily recalibration - 08:00 UTC"
    },
    {
        "schedule": "0 0 * * *",
        "command": f"python3 {REPO_ROOT}/scripts/autonomous_phase_manager.py",
        "description": "Phase progression - midnight UTC"
    },

    # Weekly Tasks
    {
        "schedule": "0 9 * * 1",
        "command": f"python3 {REPO_ROOT}/scripts/weekly_summary.py",
        "description": "Weekly summary - Monday 09:00 UTC"
    },
]

# Log directory
LOG_DIR = "/var/log/hands-off"


def get_current_crontab():
    """Get current crontab content."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout
        return ""
    except:
        return ""


def install_cron_jobs():
    """Install all cron jobs."""
    print("Installing cron jobs for autonomous system...")

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Get current crontab
    current = get_current_crontab()

    # Build new crontab
    lines = []

    # Keep existing entries that aren't ours
    for line in current.split('\n'):
        if line.strip() and not line.startswith('#'):
            if str(REPO_ROOT) not in line and 'hands-off' not in line.lower():
                lines.append(line)

    # Add header
    lines.append("")
    lines.append("# ============================================")
    lines.append("# HANDS-OFF ENGINE - Autonomous System")
    lines.append("# ============================================")
    lines.append("")

    # Add environment
    lines.append("# Environment")
    lines.append("SHELL=/bin/bash")
    lines.append("PATH=/usr/local/bin:/usr/bin:/bin")
    lines.append("")

    # Add our jobs
    for job in CRON_JOBS:
        # Generate log file name from description
        log_name = job["description"].split(" - ")[0].lower().replace(" ", "_")
        log_file = f"{LOG_DIR}/{log_name}.log"

        lines.append(f"# {job['description']}")
        lines.append(f"{job['schedule']} {job['command']} >> {log_file} 2>&1")
        lines.append("")

    # Write new crontab
    new_crontab = '\n'.join(lines)

    try:
        process = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            text=True
        )
        process.communicate(input=new_crontab)

        if process.returncode == 0:
            print(f"✓ Installed {len(CRON_JOBS)} cron jobs")
            return True
        else:
            print("✗ Failed to install crontab")
            return False
    except Exception as e:
        print(f"✗ Error installing crontab: {e}")
        return False


def list_cron_jobs():
    """List configured cron jobs."""
    print("Configured cron jobs:")
    print("-" * 60)
    for job in CRON_JOBS:
        print(f"  {job['schedule']:15} {job['description']}")
    print("-" * 60)
    print(f"Total: {len(CRON_JOBS)} jobs")


def remove_cron_jobs():
    """Remove hands-off engine cron jobs."""
    print("Removing hands-off engine cron jobs...")

    current = get_current_crontab()
    lines = []

    skip_next = False
    for line in current.split('\n'):
        if 'HANDS-OFF ENGINE' in line:
            skip_next = True
            continue
        if skip_next and line.strip().startswith('#'):
            continue
        if str(REPO_ROOT) in line or 'hands-off' in line.lower():
            continue
        skip_next = False
        lines.append(line)

    new_crontab = '\n'.join(lines)

    try:
        process = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            text=True
        )
        process.communicate(input=new_crontab)

        if process.returncode == 0:
            print("✓ Removed hands-off engine cron jobs")
            return True
        else:
            print("✗ Failed to update crontab")
            return False
    except Exception as e:
        print(f"✗ Error updating crontab: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: auto_setup_cron.py [--install|--list|--remove]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "--install":
        success = install_cron_jobs()
        sys.exit(0 if success else 1)
    elif command == "--list":
        list_cron_jobs()
    elif command == "--remove":
        success = remove_cron_jobs()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        print("Usage: auto_setup_cron.py [--install|--list|--remove]")
        sys.exit(1)


if __name__ == "__main__":
    main()
