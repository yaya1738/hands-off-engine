"""Factory development execution adapter.

The Factory remains the authority for *what* may be developed.  This adapter
only translates an already-authorized development task into a durable external
execution request.  It deliberately does not edit the repository itself.

The first implementation targets GitHub Issues because that gives us a
persistent, auditable hand-off to a coding agent while keeping execution
reversible (the agent works on a branch/PR rather than directly on main).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class DevelopmentRequestSink(Protocol):
    def submit(self, request: Dict[str, Any]) -> Dict[str, Any]: ...


@dataclass
class DevelopmentExecutionAdapter:
    """Translate an approved Factory task into an external execution request."""

    sink: Optional[DevelopmentRequestSink] = None

    def build_request(self, task: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(task, dict):
            raise TypeError("task must be a dictionary")

        task_id = task.get("id") or task.get("task_id")
        objective = task.get("objective") or task.get("goal")
        if not task_id:
            raise ValueError("authorized development task requires id/task_id")
        if not objective:
            raise ValueError("authorized development task requires objective/goal")

        canonical = json.dumps(task, sort_keys=True, default=str)
        request_id = "devreq-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]

        return {
            "request_id": request_id,
            "task_id": task_id,
            "objective": objective,
            "task": task,
            "execution_mode": "external_coding_agent_pr",
            "mutation_boundary": "isolated_branch",
            "validation_required": True,
            "merge_policy": "factory_validation_required",
            "authority": "FactoryRuntime",
        }

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        request = self.build_request(task)

        if self.sink is None:
            return {
                "status": "EXECUTION_REQUEST_READY",
                "request": request,
                "handoff": "github_coding_agent",
            }

        result = self.sink.submit(request)
        return {
            "status": "EXECUTION_REQUEST_SUBMITTED",
            "request": request,
            "result": result,
        }
