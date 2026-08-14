from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryAutonomousScheduler:
    """Persistent autonomous work queue routed through Factory authority."""

    STATE_FILE = Path("state/factory_autonomous_scheduler.json")

    def __init__(self, authority=None, state_file: Optional[Path] = None):
        self.authority = authority or FactoryAuthorityGateway()
        self.state_file = Path(state_file or self.STATE_FILE)
        self.tasks: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []
        self._load_state()

    def _load_state(self) -> None:
        if not self.state_file.exists():
            return
        try:
            state = json.loads(self.state_file.read_text())
            self.tasks = list(state.get("tasks", []))
            self._history = list(state.get("history", []))
        except (OSError, ValueError, TypeError):
            # Corrupt scheduler state must not prevent the autonomous loop starting.
            self.tasks = []
            self._history = []

    def _persist(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"tasks": self.tasks, "history": self._history[-200:]}
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
        tmp.replace(self.state_file)

    def schedule_task(self, task: Dict[str, Any]):
        if not isinstance(task, dict):
            raise TypeError("task must be a dictionary")
        if not str(task.get("objective", "")).strip():
            raise ValueError("task objective is required")

        queued = {
            **task,
            "objective": str(task["objective"]).strip(),
            "status": "pending",
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
        self.tasks.append(queued)
        self._history.append({"event": "scheduled", "task": queued})
        self._persist()
        return {"scheduled": True, "task": queued}

    def run_cycle(self):
        """Execute the next pending objective through the authoritative gateway."""
        pending = next(
            (task for task in self.tasks if task.get("status") == "pending"),
            None,
        )
        if pending is None:
            result = {"cycle_run": True, "task_count": 0, "executed": False}
            self._history.append({"event": "cycle_idle", "result": result})
            self._persist()
            return result

        pending["status"] = "running"
        pending["started_at"] = datetime.now(timezone.utc).isoformat()
        self._persist()

        try:
            execution = self.authority.execute_autonomous(pending["objective"])
            pending["status"] = (
                "completed" if execution.get("status") != "blocked" else "blocked"
            )
            pending["result"] = execution
            pending["completed_at"] = datetime.now(timezone.utc).isoformat()
            result = {"cycle_run": True, "task_count": 1, "executed": True, "task": pending}
            self._history.append({"event": "cycle_completed", "result": result})
            self._persist()
            return result
        except Exception as exc:
            pending["status"] = "failed"
            pending["error"] = str(exc)
            pending["completed_at"] = datetime.now(timezone.utc).isoformat()
            self._history.append({"event": "cycle_failed", "task": pending})
            self._persist()
            raise

    def run_self_improvement(self):
        return self.authority.execute_autonomous(
            "Run the Factory self-improvement cycle and apply only authorized improvements."
        )

    def prioritize_schedule(self):
        result = {
            "priority_task": next(
                (task for task in self.tasks if task.get("status") == "pending"),
                None,
            ),
        }
        self._history.append({"event": "prioritized", "result": result})
        self._persist()
        return result

    def history(self):
        return self._history
