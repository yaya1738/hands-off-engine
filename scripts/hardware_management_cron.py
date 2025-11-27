#!/usr/bin/env python3
"""
Hardware Management Cron - Unified Infrastructure Automation

This script runs periodically (via cron) to ensure:
1. All droplets are healthy and accessible
2. Infrastructure scales with revenue milestones
3. Hardware acquisition is triggered automatically
4. Self-healing fixes common issues autonomously

Recommended cron schedule:
  */15 * * * * /usr/bin/python3 /path/to/hardware_management_cron.py

This is the central orchestrator for self-hardware management.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import requests

REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"

# Revenue thresholds that trigger hardware acquisition
ACQUISITION_TRIGGERS = {
    "first_droplet": {
        "revenue_threshold": 0,
        "description": "Initial infrastructure - already provisioned"
    },
    "redundancy_droplet": {
        "revenue_threshold": 500,
        "description": "Add redundancy for reliability"
    },
    "scaling_droplet": {
        "revenue_threshold": 2000,
        "description": "Scale for increased load"
    },
    "premium_infrastructure": {
        "revenue_threshold": 5000,
        "description": "Upgrade to premium tier"
    },
    "enterprise_cluster": {
        "revenue_threshold": 10000,
        "description": "Full enterprise redundancy"
    }
}


def get_current_revenue() -> float:
    """Get current monthly revenue estimate."""
    try:
        # Try revenue projection first
        revenue_file = STATE_DIR / "revenue_projection.json"
        if revenue_file.exists():
            with open(revenue_file) as f:
                data = json.load(f)
                return data.get("total_monthly_potential", 0)

        # Fallback to trading performance
        perf_file = LOGS_DIR / "trading_performance.jsonl"
        if perf_file.exists():
            total_pnl = 0
            with open(perf_file) as f:
                for line in f:
                    try:
                        trade = json.loads(line)
                        total_pnl += trade.get("pnl", 0)
                    except:
                        continue
            return max(0, total_pnl * 4)

    except Exception as e:
        print(f"[error] Getting revenue: {e}")

    return 0


def get_acquisition_state() -> dict:
    """Get current acquisition state."""
    state_file = STATE_DIR / "acquisition_state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {
        "milestones_reached": [],
        "acquisitions": [],
        "last_check": None
    }


def save_acquisition_state(state: dict):
    """Save acquisition state."""
    state_file = STATE_DIR / "acquisition_state.json"
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["last_check"] = datetime.utcnow().isoformat() + "Z"
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def check_acquisition_triggers(revenue: float, state: dict) -> list:
    """Check which acquisition triggers should fire."""
    triggers_to_fire = []

    for trigger_name, config in ACQUISITION_TRIGGERS.items():
        if trigger_name in state.get("milestones_reached", []):
            continue  # Already triggered

        if revenue >= config["revenue_threshold"]:
            triggers_to_fire.append({
                "name": trigger_name,
                "threshold": config["revenue_threshold"],
                "description": config["description"]
            })

    return triggers_to_fire


def run_infrastructure_scaler(command: str = None) -> dict:
    """Run the autonomous infrastructure manager."""
    try:
        # Use the comprehensive infrastructure module
        cmd = ["python3", "-m", "infrastructure.autonomous_infra_manager"]
        if command == "status":
            cmd.append("--status")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(REPO_ROOT)
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"error": str(e)}


def run_self_healing(once: bool = True) -> dict:
    """Run the self-healing agent."""
    healing_script = REPO_ROOT / "scripts" / "self_healing_agent.py"

    if not healing_script.exists():
        return {"error": "Self-healing agent not found"}

    try:
        cmd = ["python3", str(healing_script)]
        if once:
            cmd.append("--once")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"error": str(e)}


def send_notification(message: str, is_milestone: bool = False):
    """Send Telegram notification."""
    token = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

    emoji = "🎉" if is_milestone else "🖥️"

    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        requests.post(url, json={
            'chat_id': chat_id,
            'text': f"{emoji} <b>Hardware Management</b>\n\n{message}",
            'parse_mode': 'HTML'
        }, timeout=10)
    except Exception as e:
        print(f"[notify-error] {e}")


def log_event(event_type: str, details: dict):
    """Log management event."""
    log_file = LOGS_DIR / "hardware_management.jsonl"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        **details
    }

    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def main():
    """Run full hardware management cycle."""
    print("=" * 60)
    print("HARDWARE MANAGEMENT CRON")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    results = {
        "started_at": datetime.utcnow().isoformat() + "Z",
        "steps": []
    }

    # Step 1: Get current revenue
    print("\n[1/4] Checking revenue...")
    revenue = get_current_revenue()
    print(f"  Current monthly revenue: ${revenue:.0f}")
    results["revenue"] = revenue

    # Step 2: Run self-healing
    print("\n[2/4] Running self-healing agent...")
    healing_result = run_self_healing(once=True)
    if healing_result.get("success"):
        print("  Self-healing completed successfully")
    else:
        print(f"  Self-healing issue: {healing_result.get('error', healing_result.get('stderr', 'unknown'))}")
    results["steps"].append({"self_healing": healing_result.get("success", False)})

    # Step 3: Run infrastructure scaler
    print("\n[3/4] Running infrastructure scaler...")
    scaler_result = run_infrastructure_scaler()
    if scaler_result.get("success"):
        print("  Infrastructure scaling completed")
    else:
        print(f"  Scaler issue: {scaler_result.get('error', 'unknown')}")
    results["steps"].append({"infrastructure_scaler": scaler_result.get("success", False)})

    # Step 4: Check acquisition triggers
    print("\n[4/4] Checking acquisition triggers...")
    state = get_acquisition_state()
    triggers = check_acquisition_triggers(revenue, state)

    if triggers:
        for trigger in triggers:
            print(f"  🎯 Trigger fired: {trigger['name']}")
            print(f"     Threshold: ${trigger['threshold']}")
            print(f"     Action: {trigger['description']}")

            # Mark as reached
            state["milestones_reached"].append(trigger["name"])
            state["acquisitions"].append({
                "trigger": trigger["name"],
                "revenue_at_trigger": revenue,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

            # Send celebration notification
            send_notification(
                f"<b>Revenue Milestone Reached!</b>\n\n"
                f"Trigger: {trigger['name']}\n"
                f"Revenue: ${revenue:.0f}\n"
                f"Action: {trigger['description']}",
                is_milestone=True
            )

            # Log event
            log_event("acquisition_trigger", trigger)

        # Save updated state
        save_acquisition_state(state)
    else:
        print("  No new acquisition triggers")

    results["triggers_fired"] = len(triggers)
    results["completed_at"] = datetime.utcnow().isoformat() + "Z"

    # Log full run
    log_event("management_cycle", results)

    print("\n" + "=" * 60)
    print("Hardware management cycle complete")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()
