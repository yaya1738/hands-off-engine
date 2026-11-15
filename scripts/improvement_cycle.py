#!/usr/bin/env python3
"""Periodic improvement workflow.

The scheduler owns the cadence for health, learning, and integrity jobs.
Node 1 owns lifecycle projection and safe improvement application.
This workflow owns candidate generation/one bounded dispatch, feedback
analysis, and approval notification checks.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
CYCLE_LOG = STATE / "improvement_cycles.json"


def run_subprocess(script):
    """Run a script and return bounded output and an explicit result."""
    parts = script.split()
    try:
        cmd = [sys.executable, str(ROOT / "scripts" / parts[0])] + parts[1:]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=30,
        )
        return {
            "success": result.returncode == 0,
            "output": (result.stdout + result.stderr).strip()[-1000:],
        }
    except Exception as exc:
        return {"success": False, "output": str(exc)[:1000]}


def main():
    now = datetime.now(timezone.utc).isoformat()
    print(f"=== IMPROVEMENT CYCLE @ {now} ===")

    # Sole owner of candidate generation, durable dedup, and one bus dispatch.
    improvement = run_subprocess("self_improvement.py")

    # Status is observational; Node 1 is the sole apply_batch owner.
    applier = run_subprocess("improvement_applier.py status")

    # Feedback and approval checks are periodic workflow responsibilities.
    feedback = run_subprocess("improvement_feedback.py analyze")
    approval = run_subprocess("improvement_approval.py check")

    cycle_result = {
        "timestamp": now,
        "improvement": improvement["success"],
        "applier_status": applier["success"],
        "feedback": feedback["success"],
        "approval": approval["success"],
    }

    STATE.mkdir(parents=True, exist_ok=True)
    history = []
    if CYCLE_LOG.exists():
        try:
            loaded = json.loads(CYCLE_LOG.read_text())
            if isinstance(loaded, list):
                history = loaded
        except Exception:
            pass
    history.append(cycle_result)
    CYCLE_LOG.write_text(json.dumps(history[-50:], indent=2) + "\n")

    if not approval["success"]:
        try:
            from scripts.telegram_bridge import send_message
            send_message("⚠️ Improvement cycle approval check failed")
        except Exception:
            pass

    print("Cycle complete")
    return cycle_result


if __name__ == "__main__":
    main()
