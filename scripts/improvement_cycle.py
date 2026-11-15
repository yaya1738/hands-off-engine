#!/usr/bin/env python3
"""Periodic improvement workflow.

The scheduler owns periodic cadence. Node 1 owns event-driven runtime work
and lifecycle projection only. This workflow is the sole owner of candidate
generation/dispatch and safe improvement application, plus feedback and
approval checks.
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
CYCLE_LOG = STATE / "improvement_cycles.json"


MAX_SUBPROCESS_OUTPUT_CHARS = 1000
SUBPROCESS_TIMEOUT_SECONDS = 30


def _read_subprocess_tail(output_file):
    output_file.seek(0, os.SEEK_END)
    size = output_file.tell()
    output_file.seek(max(0, size - MAX_SUBPROCESS_OUTPUT_CHARS), os.SEEK_SET)
    return output_file.read(MAX_SUBPROCESS_OUTPUT_CHARS).decode("utf-8", errors="replace").strip()


def run_subprocess(script):
    """Run a workflow child with file-backed output and process-group timeout cleanup."""
    parts = script.split()
    process = None
    try:
        cmd = [sys.executable, str(ROOT / "scripts" / parts[0])] + parts[1:]
        with tempfile.TemporaryFile(mode="w+b") as output_file:
            process = subprocess.Popen(
                cmd,
                stdout=output_file,
                stderr=subprocess.STDOUT,
                cwd=str(ROOT),
                start_new_session=True,
            )
            try:
                returncode = process.wait(timeout=SUBPROCESS_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired as exc:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                detail = (_read_subprocess_tail(output_file) + "\\n" + str(exc)).strip()
                return {"success": False, "output": detail[-MAX_SUBPROCESS_OUTPUT_CHARS:]}

            return {
                "success": returncode == 0,
                "output": _read_subprocess_tail(output_file),
            }
    except Exception as exc:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        return {"success": False, "output": str(exc)[-MAX_SUBPROCESS_OUTPUT_CHARS:]}


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
