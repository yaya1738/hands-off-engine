#!/usr/bin/env python3
"""
System Dashboard - Unified Status View
Shows all system capabilities and status at a glance.

Serving: Yair Siegel
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"


def get_financial_status() -> Dict:
    """Get current financial state."""
    try:
        with open(STATE_DIR / "financial_state.json") as f:
            return json.load(f)
    except:
        return {"balance": "unknown", "positions_value": "unknown"}


def get_system_health() -> Dict:
    """Get system health metrics."""
    try:
        # Check running processes
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=5
        )
        python_procs = len([l for l in result.stdout.split('\n') if 'python' in l.lower()])

        # Check disk
        disk = subprocess.run(
            ["df", "-h", "/"], capture_output=True, text=True, timeout=5
        )
        disk_line = disk.stdout.strip().split('\n')[-1].split()

        # Check memory
        mem = subprocess.run(
            ["free", "-h"], capture_output=True, text=True, timeout=5
        )
        mem_line = mem.stdout.strip().split('\n')[1].split()

        return {
            "python_processes": python_procs,
            "disk_used": disk_line[2] if len(disk_line) > 2 else "unknown",
            "disk_available": disk_line[3] if len(disk_line) > 3 else "unknown",
            "memory_used": mem_line[2] if len(mem_line) > 2 else "unknown",
            "memory_available": mem_line[3] if len(mem_line) > 3 else "unknown"
        }
    except Exception as e:
        return {"error": str(e)}


def get_autonomous_status() -> Dict:
    """Get status of autonomous systems."""
    systems = {
        "enhanced_loop": STATE_DIR / "enhanced_loop_state.json",
        "income_accelerator": STATE_DIR / "income_accelerator.json",
        "active_pursuit": STATE_DIR / "active_pursuit.json",
        "conversion_optimizer": STATE_DIR / "conversion_optimizer.json",
        "reality_feedback": STATE_DIR / "reality_feedback.json",
        "self_modification": STATE_DIR / "self_modification_state.json"
    }

    status = {}
    for name, path in systems.items():
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                    status[name] = {
                        "active": True,
                        "last_update": data.get("last_updated", data.get("last_run", "unknown"))
                    }
            except:
                status[name] = {"active": False, "error": "parse_failed"}
        else:
            status[name] = {"active": False, "error": "no_state_file"}

    return status


def get_cron_status() -> Dict:
    """Get cron job status."""
    try:
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True, timeout=5
        )
        jobs = [l.strip() for l in result.stdout.split('\n') if l.strip() and not l.startswith('#')]
        return {
            "total_jobs": len(jobs),
            "samples": jobs[:5]
        }
    except:
        return {"error": "failed to read crontab"}


def get_capability_summary() -> Dict:
    """Get summary of all capabilities."""
    return {
        "autonomous_systems": [
            "enhanced_loop - Full system orchestration",
            "income_accelerator - Revenue generation",
            "web_executor - Web outreach",
            "active_pursuit - Opportunity hunting",
            "conversion_optimizer - A/B testing",
            "reality_feedback - External tracking",
            "self_healer - Auto-repair",
            "self_modification - Code improvement"
        ],
        "income_paths": [
            "Freelance (Upwork, Fiverr)",
            "Trading (Polymarket - DRYRUN)",
            "Content (LinkedIn, Reddit, HN)",
            "GitHub contributions"
        ],
        "installed_packages": [
            "python-dotenv",
            "aiohttp",
            "praw (Reddit)",
            "tweepy (Twitter)",
            "requests"
        ]
    }


def print_dashboard():
    """Print the full dashboard."""
    print("=" * 70)
    print("SYSTEM DASHBOARD - HANDS-OFF ENGINE")
    print(f"Master: {MASTER}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)
    print()

    # Financial
    print("[FINANCIAL STATUS]")
    fin = get_financial_status()
    print(f"  Balance: ${fin.get('balance', 'unknown')}")
    print(f"  Positions: ${fin.get('positions_value', 'unknown')}")
    print(f"  Mode: {fin.get('system_mode', 'unknown')}")
    print()

    # Health
    print("[SYSTEM HEALTH]")
    health = get_system_health()
    print(f"  Python processes: {health.get('python_processes', 'unknown')}")
    print(f"  Disk: {health.get('disk_used', '?')}/{health.get('disk_available', '?')}")
    print(f"  Memory: {health.get('memory_used', '?')}/{health.get('memory_available', '?')}")
    print()

    # Autonomous systems
    print("[AUTONOMOUS SYSTEMS]")
    auto = get_autonomous_status()
    for name, status in auto.items():
        icon = "✓" if status.get("active") else "✗"
        print(f"  {icon} {name}: {status.get('last_update', status.get('error', 'unknown'))[:30]}")
    print()

    # Cron
    print("[SCHEDULED JOBS]")
    cron = get_cron_status()
    print(f"  Total jobs: {cron.get('total_jobs', 0)}")
    print()

    # Capabilities
    print("[CAPABILITIES]")
    caps = get_capability_summary()
    print(f"  Autonomous systems: {len(caps['autonomous_systems'])}")
    print(f"  Income paths: {len(caps['income_paths'])}")
    print(f"  Packages: {len(caps['installed_packages'])}")
    print()

    # Next actions
    print("[RECOMMENDED ACTIONS]")
    print("  1. Post on Hacker News: https://news.ycombinator.com/submit")
    print("  2. Apply to Upwork: https://upwork.com/nx/search/jobs/?q=trading%20bot")
    print("  3. Post on r/algotrading: https://reddit.com/r/algotrading")
    print("  4. Enable GitHub Sponsors: https://github.com/sponsors")
    print()

    return {
        "financial": fin,
        "health": health,
        "autonomous": auto,
        "cron": cron,
        "capabilities": caps
    }


def main():
    return print_dashboard()


if __name__ == "__main__":
    main()
