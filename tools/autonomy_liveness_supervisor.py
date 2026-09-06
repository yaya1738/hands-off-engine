from __future__ import annotations

import json
import signal
import time
from pathlib import Path
from datetime import datetime, timezone

from ai.factory.autonomous_objective_loop import FactoryAutonomousObjectiveLoop
from ai.factory.runtime import FactoryRuntime

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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
        }
    )

    selected = selection.get("selected")
    queued = False
    task_id = None
    if isinstance(selected, dict) and selected.get("objective"):
        objective_id = selected.get("strategic_objective_id", "")
        queue = AutonomousTaskQueue(repo_root)
        pending = queue.get_all_tasks()
        duplicate = any(
            isinstance(task, dict)
            and task.get("metadata", {}).get("objective") == selected.get("objective")
            for task in pending
        )
        if not duplicate:
            task_id = queue.add_task(
                title=f"Autonomous objective: {selected['objective']}",
                description=(
                    "Pursue the selected autonomous objective through existing "
                    "FactoryAuthorityGateway and safety boundaries. Assess first, "
                    "make only bounded authorized changes, test, verify, recover "
                    "from failures, and communicate only material decisions or blockers. "
                    "Do not bypass approval, credentials, execution, or live-mutation gates."
                ),
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

    return {
        "timestamp": utc_now(),
        "status": "active",
        "selection": selection,
        "task_queued": queued,
        "task_id": task_id,
    }


def persist(repo_root: Path, state: dict) -> None:
    path = repo_root / STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    signal.signal(signal.SIGALRM, _timeout_handler)

    while True:
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
        time.sleep(max(1, INTERVAL_SECONDS - int(state["cycle_duration_seconds"])))


if __name__ == "__main__":
    raise SystemExit(main())
