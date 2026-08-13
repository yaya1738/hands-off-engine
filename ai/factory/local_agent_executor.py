from pathlib import Path
from typing import Any, Dict, Optional


class FactoryLocalAgentExecutor:
    """Explicit boundary for bounded local-agent execution.

    The executor does not grant the model repository-wide authority. A caller
    must provide an explicit workspace, allowed paths, and an injected agent
    callable. The callable receives the task plus the authorization envelope.
    """

    def __init__(self, agent: Optional[Any] = None):
        self.agent = agent
        self.executions = []

    def execute(
        self,
        task: Dict[str, Any],
        workspace: str = ".",
        allowed_paths=None,
    ):
        allowed_paths = tuple(allowed_paths or task.get("allowed_paths", ()))

        if self.agent is None:
            result = {
                "status": "AGENT_UNAVAILABLE",
                "task": task,
                "workspace": str(Path(workspace).resolve()),
                "allowed_paths": list(allowed_paths),
            }
            self.executions.append(result)
            return result

        envelope = {
            "task": task,
            "workspace": str(Path(workspace).resolve()),
            "allowed_paths": list(allowed_paths),
        }

        result = self.agent(envelope)
        if not isinstance(result, dict):
            raise TypeError("local agent must return a dictionary")

        result = {
            **result,
            "task": task,
            "workspace": envelope["workspace"],
            "allowed_paths": list(allowed_paths),
        }
        self.executions.append(result)
        return result

    def report(self):
        return {
            "executions": self.executions,
            "count": len(self.executions),
        }
