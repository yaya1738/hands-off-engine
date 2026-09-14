#!/usr/bin/env python3
"""Periodic Improvement Cycle — runs all monitoring and improvement subsystems.

Ties together: health monitor → learning loop → self-improvement → state integrity.
Sends a summary to Telegram and posts results to the bus.

Intended to run every N minutes via cron or Termux scheduler.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
CYCLE_LOG = STATE / "improvement_cycles.json"


def run_subprocess(script):
    """Run a script and return its output. Supports 'script.py arg1 arg2' format."""
    parts = script.split()
    try:
        cmd = [sys.executable, str(ROOT / "scripts" / parts[0])] + parts[1:]
        r = subprocess.run(
            cmd,
            capture_output=True, text=True, cwd=str(ROOT), timeout=30
        )
        return {"success": r.returncode == 0, "output": (r.stdout + r.stderr).strip()}
    except Exception as e:
        return {"success": False, "output": str(e)}


def main():
    now = datetime.now(timezone.utc).isoformat()
    
    print(f"=== IMPROVEMENT CYCLE @ {now} ===")
    
    # 1. Health check
    health = run_subprocess("health_monitor.py")
    print(f"Health: {'✅' if health['success'] else '⚠️'}")
    
    # 2. Learning analysis
    learning = run_subprocess("learning_loop.py")
    
    # 3. Self-improvement
    improvement = run_subprocess("self_improvement.py")
    
    # 4. State integrity
    integrity = run_subprocess("state_integrity.py")
    
    # 5. Improvement applier (apply safe improvements)
    applier = run_subprocess("improvement_applier.py status")
    
    # 6. Feedback analysis (measure improvement impact)
    feedback = run_subprocess("improvement_feedback.py analyze")
    
    # 7. Approval check (notify operator of pending risky improvements)
    approval = run_subprocess("improvement_approval.py check")
    
    # Load results
    cycle_result = {
        "timestamp": now,
        "health": health["success"],
        "learning": learning["success"],
        "improvement": improvement["success"],
        "integrity": integrity["success"],
        "applier": applier["success"],
        "feedback": feedback["success"],
        "approval": approval["success"],
    }
    
    # Save cycle history
    STATE.mkdir(parents=True, exist_ok=True)
    history = []
    if CYCLE_LOG.exists():
        try:
            history = json.loads(CYCLE_LOG.read_text())
        except Exception:
            pass
    history.append(cycle_result)
    if len(history) > 50:
        history = history[-50:]
    CYCLE_LOG.write_text(json.dumps(history, indent=2) + "\n")
    
    # Send Telegram alert only if something's wrong
    issues = []
    if not health["success"]:
        issues.append("health check failed")
    if not integrity["success"]:
        issues.append("state integrity check failed")
    
    if issues:
        try:
            from scripts.telegram_bridge import send_message
            send_message(f"⚠️ Improvement cycle issues: {', '.join(issues)}")
        except Exception:
            pass
    
    print(f"Cycle complete: {'ALL OK' if not issues else 'ISSUES: ' + ', '.join(issues)}")
    return cycle_result


if __name__ == "__main__":
    main()
