from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from ai.factory.autonomous_objective_loop import FactoryAutonomousObjectiveLoop
from ai.factory.authority_gateway import FactoryAuthorityGateway
from ai.factory.runtime import FactoryRuntime
from scripts.autonomous_task_queue import AutonomousTaskQueue


INTERVAL_SECONDS = 10 * 60
CYCLE_TIMEOUT_SECONDS = 5 * 60
STATE_PATH = Path("state/autonomy_liveness.json")


class CycleTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise CycleTimeout("autonomous objective cycle exceeded timeout")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _successful_objectives(repo_root: Path) -> set[str]:
    """Return objectives whose prior autonomous execution completed successfully."""
    path = repo_root / "state" / "autonomous_tasks_completed.jsonl"
    if not path.exists():
        return set()

    completed: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            task = record.get("task", {})
            metadata = task.get("metadata", {}) if isinstance(task, dict) else {}
            result = json.loads(record.get("result", "{}"))
            if (
                isinstance(metadata, dict)
                and metadata.get("objective")
                and isinstance(result, dict)
                and result.get("status") == "executed"
                and result.get("success") is True
            ):
                completed.add(str(metadata["objective"]).strip().casefold())
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return completed


def run_cycle(repo_root: Path) -> dict:
    runtime = FactoryRuntime()
    discovery = runtime.autonomy.discovery_gate(
        "discover the highest-value next autonomous objective",
        "anti-dormancy liveness supervisor",
    )

    gaps = []
    graph = discovery.get("capability_graph_analysis", {})
    if isinstance(graph, dict):
        gaps.extend(graph.get("gaps", []))

    queue = AutonomousTaskQueue(repo_root)
    pending_task = queue.get_next_task()
    retired = _successful_objectives(repo_root)
    selection = FactoryAutonomousObjectiveLoop(runtime).select_next(
        {
            "strategic_objective": (
                "Continuously increase autonomous capability so routine operation "
                "requires progressively less human intervention, while continuously "
                "improve the system's ability to communicate dynamically, selectively, "
                "clearly, and powerfully with Yair when human input has genuine value."
            ),
            "gaps": gaps,
            "discovery": discovery,
            "excluded_objectives": retired,
        }
    )

    selected = selection.get("selected")
    queued = False
    task_id = None
    execution = None
    execution_observed = False
    verification_observed = False
    execution_succeeded = False

    # Authenticated external requests are durable work, not merely messages.
    # They take precedence over generated objectives so Telegram/web ingress can
    # drive the same governed execution loop without a ChatGPT session.
    if pending_task:
        objective = pending_task.get("description") or pending_task.get("title")
        selected = {
            "objective": objective,
            "strategic_objective_id": pending_task.get("metadata", {}).get("objective_id", "external-request"),
            "score": 100,
            "source": pending_task.get("source", "external"),
            "task_id": pending_task.get("id"),
        }
        task_id = pending_task.get("id")
    elif isinstance(selected, dict) and selected.get("objective"):
        objective_id = selected.get("strategic_objective_id", "")
        pending = queue.get_all_tasks()
        duplicate = any(
            isinstance(task, dict)
            and task.get("metadata", {}).get("objective") == selected.get("objective")
            for task in pending
        )
        if not duplicate:
            task_id = queue.add_task(
                title=f"Autonomous objective: {selected['objective']}",
                description=selected["objective"],
                priority="high" if selected.get("score", 0) >= 95 else "normal",
                source="autonomous_objective_liveness",
                metadata={
                    "objective": selected.get("objective"),
                    "objective_id": objective_id,
                    "score": selected.get("score"),
                    "authority": "FactoryAuthorityGateway",
                },
            )
            queued = True

    if isinstance(selected, dict) and selected.get("objective"):
        gateway = FactoryAuthorityGateway(runtime=runtime)
        execution = gateway.execute_autonomous(selected["objective"])
        execution_observed = isinstance(execution, dict) and bool(execution.get("execution"))
        runtime_execution = execution.get("execution", {}) if isinstance(execution, dict) else {}
        verification_observed = execution_observed and isinstance(runtime_execution, dict) and "success" in runtime_execution
        execution_succeeded = verification_observed and runtime_execution.get("success") is True

        if task_id and execution_observed:
            completion = {
                "status": "executed",
                "success": runtime_execution.get("success"),
                "steps_completed": runtime_execution.get("steps_completed", []),
            }
            queue.complete_task(task_id, result=json.dumps(completion, sort_keys=True))
            if pending_task:
                # External requests receive completion feedback on their original
                # control surface. Notification failure never falsifies execution.
                try:
                    from telegram.autonomy_notifier import notify_task_result
                    notify_task_result(pending_task, execution)
                except Exception:
                    pass

    return {
        "timestamp": utc_now(),
        "status": "observed" if execution_observed else "degraded" if selected else "idle",
        "selection": selection,
        "retired_successful_objective_count": len(retired),
        "task_queued": queued,
        "task_id": task_id,
        "external_task_processed": bool(pending_task),
        "execution_observed": execution_observed,
        "verification_observed": verification_observed,
        "execution_succeeded": execution_succeeded,
        # This flag deliberately requires an explicit successful runtime result;
        # execution alone must never be represented as successful live activity.
        "live_system_active": execution_succeeded,
        "claim_basis": (
            "observed autonomous execution with explicit successful runtime result; external side effects not independently proven"
            if execution_succeeded
            else "observed autonomous execution with unsuccessful or non-success runtime result"
            if execution_observed
            else "no executable objective selected"
            if not selected
            else "no observed autonomous execution"
        ),
        "execution": execution,
    }


def persist(repo_root: Path, state: dict) -> None:
    path = repo_root / STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def run_once(repo_root: Path) -> dict:
    """Execute exactly one autonomous cycle and persist its evidence."""
    started = time.monotonic()
    try:
        signal.alarm(CYCLE_TIMEOUT_SECONDS)
        state = run_cycle(repo_root)
        signal.alarm(0)
    except CycleTimeout as exc:
        signal.alarm(0)
        state = {"timestamp": utc_now(), "status": "degraded", "error": str(exc)}
    except Exception as exc:
        signal.alarm(0)
        state = {"timestamp": utc_now(), "status": "degraded", "error": str(exc)}

    state["cycle_duration_seconds"] = round(time.monotonic() - started, 3)
    persist(repo_root, state)
    print(json.dumps(state, sort_keys=True), flush=True)
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the autonomous liveness supervisor continuously or once."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="execute one governed autonomous cycle and exit",
    )
    args = parser.parse_args(argv)

    repo_root = REPO_ROOT
    signal.signal(signal.SIGALRM, _timeout_handler)

    if args.once:
        run_once(repo_root)
        return 0

    while True:
        run_once(repo_root)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
