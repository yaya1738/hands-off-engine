from datetime import datetime, timezone
from typing import Any, Dict


class FactoryStateSnapshot:
    def create(
        self,
        projects: Any,
        tasks: Any,
        artifacts: Any,
        metrics: Dict[str, Any],
        health: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "projects": projects,
            "tasks": tasks,
            "artifacts": artifacts,
            "metrics": metrics,
            "health": health,
        }
