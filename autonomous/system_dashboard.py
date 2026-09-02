#!/usr/bin/env python3
"""Read-only system dashboard; operational actions belong to FactoryAuthorityGateway."""

import json
from datetime import datetime, timezone
from pathlib import Path
from shutil import disk_usage
from typing import Dict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
MASTER = "Yair Siegel"


def get_financial_status() -> Dict:
    try:
        with open(STATE_DIR / "financial_state.json") as f:
            return json.load(f)
    except Exception:
        return {"balance": "unknown", "positions_value": "unknown"}


def get_system_health() -> Dict:
    """Use in-process read-only APIs; never spawn diagnostic commands."""
    try:
        usage = disk_usage(PROJECT_ROOT)
        available = usage.free
        used = usage.used
        python_procs = "unknown"
        proc = Path("/proc")
        if proc.exists():
            python_procs = sum(
                1 for p in proc.iterdir()
                if p.name.isdigit() and (p / "comm").exists()
                and "python" in (p / "comm").read_text(errors="ignore").lower()
            )
        return {
            "python_processes": python_procs,
            "disk_used": f"{used / (1024**3):.1f}G",
            "disk_available": f"{available / (1024**3):.1f}G",
            "memory_used": "unknown",
            "memory_available": "unknown",
        }
    except Exception as exc:
        return {"error": str(exc)}


def get_autonomous_status() -> Dict:
    systems = {
        "enhanced_loop": STATE_DIR / "enhanced_loop_state.json",
        "income_accelerator": STATE_DIR / "income_accelerator.json",
        "active_pursuit": STATE_DIR / "active_pursuit.json",
        "conversion_optimizer": STATE_DIR / "conversion_optimizer.json",
        "reality_feedback": STATE_DIR / "reality_feedback.json",
        "self_modification": STATE_DIR / "self_modification_state.json",
    }
    status = {}
    for name, path in systems.items():
        if path.exists():
            try:
                data = json.loads(path.read_text())
                status[name] = {"active": True, "last_update": data.get("last_updated", data.get("last_run", "unknown"))}
            except Exception:
                status[name] = {"active": False, "error": "parse_failed"}
        else:
            status[name] = {"active": False, "error": "no_state_file"}
    return status


def get_cron_status() -> Dict:
    """Cron mutation/inspection remains an authority-owned operation."""
    return {
        "total_jobs": "unknown",
        "samples": [],
        "error": "[FACTORY-AUTHORITY] cron inspection is disabled in legacy dashboard; use FactoryAuthorityGateway",
    }


def get_capability_summary() -> Dict:
    return {
        "autonomous_systems": ["enhanced_loop", "income_accelerator", "web_executor", "active_pursuit", "conversion_optimizer", "reality_feedback", "self_healer", "self_modification"],
        "income_paths": ["Freelance", "Trading (Polymarket - DRYRUN)", "Content", "GitHub contributions"],
        "installed_packages": ["python-dotenv", "aiohttp", "praw", "tweepy", "requests"],
    }


def print_dashboard():
    print("=" * 70)
    print("SYSTEM DASHBOARD - HANDS-OFF ENGINE")
    print(f"Master: {MASTER}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)
    fin = get_financial_status()
    health = get_system_health()
    auto = get_autonomous_status()
    cron = get_cron_status()
    caps = get_capability_summary()
    print(f"\n[FINANCIAL STATUS]\n  Balance: ${fin.get('balance', 'unknown')}\n  Positions: ${fin.get('positions_value', 'unknown')}\n  Mode: {fin.get('system_mode', 'unknown')}")
    print(f"\n[SYSTEM HEALTH]\n  Python processes: {health.get('python_processes', 'unknown')}\n  Disk: {health.get('disk_used', '?')}/{health.get('disk_available', '?')}\n  Memory: {health.get('memory_used', '?')}/{health.get('memory_available', '?')}")
    print("\n[AUTONOMOUS SYSTEMS]")
    for name, status in auto.items():
        print(f"  {'✓' if status.get('active') else '✗'} {name}: {str(status.get('last_update', status.get('error', 'unknown')))[:30]}")
    print(f"\n[SCHEDULED JOBS]\n  Total jobs: {cron.get('total_jobs', 0)}")
    print(f"\n[CAPABILITIES]\n  Autonomous systems: {len(caps['autonomous_systems'])}\n  Income paths: {len(caps['income_paths'])}\n  Packages: {len(caps['installed_packages'])}")
    return {"financial": fin, "health": health, "autonomous": auto, "cron": cron, "capabilities": caps}


def main():
    return print_dashboard()


if __name__ == "__main__":
    main()
