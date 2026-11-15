#!/usr/bin/env python3
"""Periodic improvement workflow.

The scheduler owns periodic cadence. Node 1 owns event-driven runtime work
and lifecycle projection only. This workflow is the sole owner of candidate
generation/dispatch and safe improvement application, plus feedback and
approval checks.
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


def apply_generated_candidates():
    """Apply the latest candidates after successful generation.

    The applier itself is the policy boundary: only SAFE_ACTIONS execute;
    RISKY_ACTIONS are queued for explicit operator approval.
    """
    candidate_file = STATE / "improvement_state.json"
    if not candidate_file.exists():
        return []

    candidate_state = json.loads(candidate_file.read_text())
    if not isinstance(candidate_state, dict):
        raise ValueError("improvement candidate state must be an object")
    candidates = candidate_state.get("improvements", [])
    if not isinstance(candidates, list):
        raise ValueError("improvement candidates must be a list")
    candidates = [
        item for item in candidates
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]
    ]

    from scripts.improvement_applier import ImprovementApplier
    applier = ImprovementApplier(repo_root=ROOT)
    return applier.apply_batch(candidates)


def main():
    now = datetime.now(timezone.utc).isoformat()
    print(f"=== IMPROVEMENT CYCLE @ {now} ===")

    # Sole owner of candidate generation, durable dedup, and one bus dispatch.
    improvement = run_subprocess("self_improvement.py")

    # Apply only after this cycle generated a fresh candidate snapshot.
    # ImprovementApplier enforces its SAFE_ACTIONS / RISKY_ACTIONS policy:
    # safe actions may run; risky actions remain queued for operator approval.
    apply_success = False
    apply_results = []
    if improvement["success"]:
        try:
            apply_results = apply_generated_candidates()
            apply_success = True
        except Exception as exc:
            print(f"Improvement apply failed: {exc}")

    # Status is observational; this cycle is the only apply_batch owner.
    applier = run_subprocess("improvement_applier.py status")

    # Feedback and approval checks are periodic workflow responsibilities.
    feedback = run_subprocess("improvement_feedback.py analyze")
    approval = run_subprocess("improvement_approval.py check")

    cycle_result = {
        "timestamp": now,
        "improvement": improvement["success"],
        "applier_apply": apply_success,
        "applied_count": sum(1 for result in apply_results if result.get("applied")),
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
