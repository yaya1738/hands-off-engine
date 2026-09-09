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
MISSION_PATH = Path("state/autonomy_mission.json")
MISSION_OBJECTIVE = (
    "Continuously improve this autonomous system itself: discover its highest-value "
    "capability gaps, repair or construct the missing capabilities, validate the "
    "result, integrate successful improvements into the governed runtime, and then "
    "repeat indefinitely with progressively less human intervention. Preserve all "
    "existing safety, authority, audit, cost, risk, and verification boundaries."
)
MISSION_PHASE: str | None = None


class CycleTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise CycleTimeout("autonomous objective cycle exceeded timeout")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_mission(repo_root: Path) -> dict:
    path = repo_root / MISSION_PATH
    if not path.exists():
        return {"mission": MISSION_OBJECTIVE, "cycle_count": 0, "last_status": "never_run", "last_error": None, "updated_at": utc_now()}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("mission state must be an object")
        data["mission"] = MISSION_OBJECTIVE
        data.setdefault("cycle_count", 0)
        return data
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {"mission": MISSION_OBJECTIVE, "cycle_count": 0, "last_status": "mission_state_recovered", "last_error": None, "updated_at": utc_now()}


def _persist_mission(repo_root: Path, mission: dict) -> None:
    path = repo_root / MISSION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mission, indent=2, sort_keys=True), encoding="utf-8")


def _successful_objectives(repo_root: Path) -> set[str]:
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
            if isinstance(metadata, dict) and metadata.get("objective") and isinstance(result, dict) and result.get("status") == "executed" and result.get("success") is True:
                completed.add(str(metadata["objective"]).strip().casefold())
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return completed


def run_cycle(repo_root: Path) -> dict:
    mission = _load_mission(repo_root)
    mission["cycle_count"] = int(mission.get("cycle_count", 0)) + 1
    mission["updated_at"] = utc_now()
    runtime = FactoryRuntime()
    discovery = runtime.autonomy.discovery_gate(mission["mission"], "persistent autonomous self-improvement supervisor")
    gaps = []
    graph = discovery.get("capability_graph_analysis", {})
    if isinstance(graph, dict):
        gaps.extend(graph.get("gaps", []))
    previous_error = mission.get("last_error")
    if previous_error:
        gaps.insert(0, {"capability": "previous_cycle_repair", "component": previous_error})
    queue = AutonomousTaskQueue(repo_root)
    pending_task = queue.get_next_task()
    retired = _successful_objectives(repo_root)
    discovery_missing = discovery.get("missing", []) if isinstance(discovery, dict) else []
    discovery_findings = discovery.get("findings", []) if isinstance(discovery, dict) else []

    # Always invoke the objective selector in the post-DASS state. The selector
    # deliberately supplies a bounded continuity objective when discovery has
    # no fresh gap/finding, preventing a false "converged" state from freezing
    # the autonomous improvement loop.
    selection = {"status": "external_task", "selected": None, "candidate_count": 0, "candidates": []} if pending_task else FactoryAutonomousObjectiveLoop(runtime).select_next({
        "strategic_objective": mission["mission"],
        "gaps": gaps,
        "discovery": {**discovery, "missing": discovery_missing, "findings": discovery_findings},
        "excluded_objectives": retired,
        "cycle_count": mission["cycle_count"],
        "phase": MISSION_PHASE,
    })

    selected = selection.get("selected")
    queued = False
    task_id = None
    execution = None
    execution_observed = False
    verification_observed = False
    execution_succeeded = False
    converged = False

    if pending_task:
        objective = pending_task.get("description") or pending_task.get("title")
        selected = {"objective": objective, "strategic_objective_id": pending_task.get("metadata", {}).get("objective_id", "external-request"), "score": 100, "source": pending_task.get("source", "external"), "task_id": pending_task.get("id")}
        task_id = pending_task.get("id")
    elif isinstance(selected, dict) and selected.get("objective"):
        objective_id = selected.get("strategic_objective_id", "")
        if selected.get("objective", "").strip().casefold() in retired:
            selected = None
        if selected is not None:
            pending = queue.get_all_tasks()
            duplicate = any(isinstance(task, dict) and task.get("metadata", {}).get("objective") == selected.get("objective") for task in pending)
            if not duplicate:
                task_id = queue.add_task(
                    title=f"Autonomous objective: {selected['objective']}", description=selected["objective"],
                    priority="high" if selected.get("score", 0) >= 95 else "normal",
                    source="autonomous_objective_liveness",
                    metadata={"objective": selected.get("objective"), "objective_id": objective_id, "score": selected.get("score"), "priority_score": selected.get("priority_score"), "authority": "FactoryAuthorityGateway", "persistent_mission": True, "dass_phase": MISSION_PHASE},
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
            completion = {"status": "executed", "success": runtime_execution.get("success"), "steps_completed": runtime_execution.get("steps_completed", [])}
            result_json = json.dumps(completion, sort_keys=True)
            if execution_succeeded:
                queue.complete_task(task_id, result=result_json)
            else:
                queue.record_attempt(task_id, result=result_json)
            if pending_task:
                try:
                    from telegram.autonomy_notifier import notify_task_result
                    notify_task_result(pending_task, execution)
                except Exception:
                    pass

    was_converged = bool(mission.get("converged"))
    mission["last_status"] = "succeeded" if execution_succeeded else "blocked_or_failed" if selected else "idle"
    mission["last_error"] = None if execution_succeeded else (execution.get("reason") if isinstance(execution, dict) else "no executable objective")
    mission["last_objective"] = selected.get("objective") if isinstance(selected, dict) else None
    mission["converged"] = False
    mission["convergence_transition"] = False if was_converged else False
    _persist_mission(repo_root, mission)

    return {
        "timestamp": utc_now(),
        "status": "observed" if execution_observed else "idle" if not selected else "degraded",
        "mission": mission,
        "selection": selection,
        "retired_successful_objective_count": len(retired),
        "task_queued": queued,
        "task_id": task_id,
        "external_task_processed": bool(pending_task),
        "execution_observed": execution_observed,
        "verification_observed": verification_observed,
        "execution_succeeded": execution_succeeded,
        "converged": False,
        "live_system_active": execution_succeeded,
        "claim_basis": "objective selected through governed autonomous objective loop; execution remains subject to FactoryAuthorityGateway" if selected else "no executable objective selected",
        "execution": execution,
    }


def persist(repo_root: Path, state: dict) -> None:
    path = repo_root / STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def run_once(repo_root: Path) -> dict:
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
    parser = argparse.ArgumentParser(description="Run the autonomous liveness supervisor continuously or once.")
    parser.add_argument("--once", action="store_true", help="execute one governed autonomous cycle and exit")
    args = parser.parse_args(argv)
    repo_root = REPO_ROOT
    signal.signal(signal.SIGALRM, _timeout_handler)
    if args.once:
        state = run_once(repo_root)
        return 0 if state.get("execution_succeeded") is True else 1
    while True:
        state = run_once(repo_root)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
