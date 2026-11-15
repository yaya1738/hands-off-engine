#!/usr/bin/env python3
"""Periodic improvement workflow.

The scheduler owns periodic cadence. Node 1 owns event-driven runtime work
and lifecycle projection only. This workflow is the sole owner of candidate
generation/dispatch and safe improvement application, plus feedback and
approval checks.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
CYCLE_LOG = STATE / "improvement_cycles.json"


MAX_SUBPROCESS_OUTPUT_CHARS = 1000
SUBPROCESS_TIMEOUT_SECONDS = 30

# Fatal failure policy: these cycle outcomes make the whole run exit
# non-zero, so scheduler.run_task() records the cycle as failed instead of
# a false green. Fatal:
#   - improvement: candidate generation failed — the cycle produced nothing.
#   - applier_apply: the apply step raised an unexpected error (integrity
#     problem with improvement_state.json / applier), not merely "no
#     candidates" or "risky actions queued".
# Non-fatal (observational; approval failures carry their own alert):
#   - applier_status, feedback, approval — diagnostics with independent
#     alerting; a failure here must not mark the whole cycle failed.
FATAL_FIELDS = ("improvement", "applier_apply")


def _send_approval_alert():
    """Best-effort approval-check alert through the real TelegramBridge API.

    The bridge handles not-configured and delivery errors internally; only
    genuinely unexpected errors are logged here instead of being swallowed.
    Returns True when an alert was actually dispatched.
    """
    try:
        from scripts.telegram_bridge import TelegramBridge
        bridge = TelegramBridge()
        result = bridge.send_alert(
            "Improvement cycle", "Approval check failed", severity="warning")
        if isinstance(result, dict) and result.get("status") == "not_configured":
            print("Telegram not configured; approval-check alert not sent")
            return False
        return isinstance(result, dict) and result.get("status") == "sent"
    except Exception as exc:
        print(f"Telegram approval alert error: {exc}")
        return False


def run_subprocess(script):
    """Run a workflow child with bounded output and owned group cleanup."""
    from scripts.process_group import run_process

    parts = script.split()
    cmd = [sys.executable, str(ROOT / "scripts" / parts[0])] + parts[1:]
    outcome = run_process(
        cmd,
        cwd=ROOT,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        max_output_chars=MAX_SUBPROCESS_OUTPUT_CHARS,
    )
    return {"success": outcome["success"], "output": outcome["output"]}


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
    """Run one improvement cycle; return a process exit code (0 success, 1 fatal failure)."""
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
        _send_approval_alert()

    print(json.dumps(cycle_result, indent=2, sort_keys=True))

    fatal = [field for field in FATAL_FIELDS if not cycle_result.get(field)]
    if fatal:
        print(f"Fatal cycle failures: {', '.join(fatal)}")
    print("Cycle complete")
    # Fatal failures must propagate to the process exit code; the scheduler
    # records cycle success from this code and must never see a false green.
    return 1 if fatal else 0


if __name__ == "__main__":
    raise SystemExit(main())
