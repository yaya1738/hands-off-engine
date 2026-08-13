from pathlib import Path
from typing import Any, Dict, Optional

from .agent_result_validator import AgentResultValidator


class FactoryLocalAgentExecutor:
    """Explicit boundary for bounded local-agent execution."""

    def __init__(self, agent: Optional[Any] = None):
        self.agent = agent
        self.executions = []

    @staticmethod
    def _validate_allowed_paths(workspace: Path, allowed_paths):
        normalized = []
        for raw_path in allowed_paths:
            path = Path(raw_path)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"allowed path escapes workspace: {raw_path}")
            candidate = (workspace / path).resolve()
            try:
                candidate.relative_to(workspace)
            except ValueError as exc:
                raise ValueError(f"allowed path escapes workspace: {raw_path}") from exc
            normalized.append(path.as_posix())
        return tuple(normalized)

    def execute(self, task: Dict[str, Any], workspace: str = ".", allowed_paths=None):
        workspace_path = Path(workspace).resolve()
        allowed_paths = self._validate_allowed_paths(
            workspace_path, tuple(allowed_paths or task.get("allowed_paths", ()))
        )

        if self.agent is None:
            result = {"status": "AGENT_UNAVAILABLE", "task": task,
                      "workspace": str(workspace_path), "allowed_paths": list(allowed_paths)}
            self.executions.append(result)
            return result

        envelope = {"task": task, "workspace": str(workspace_path),
                    "allowed_paths": list(allowed_paths)}
        raw_result = self.agent(envelope)
        if isinstance(raw_result, dict) and raw_result.get("status") == "agent_completed":
            validated = AgentResultValidator.validate(raw_result.get("response"), allowed_paths)
            result = {"status": "agent_completed", "edit": validated}
        else:
            if not isinstance(raw_result, dict):
                raise TypeError("local agent must return a dictionary")
            result = raw_result

        result = {**result, "task": task, "workspace": envelope["workspace"],
                  "allowed_paths": list(allowed_paths)}
        self.executions.append(result)
        return result

    def report(self):
        return {"executions": self.executions, "count": len(self.executions)}
