from typing import Any, Dict


class FactoryIDEModel:
    def build(
        self,
        workspace: Any,
        runtime: Any,
        metrics: Dict[str, Any],
        events: Any,
        recommendations: Any,
    ) -> Dict[str, Any]:

        return {
            "projects": workspace.list_projects(),
            "health": runtime.status(),
            "metrics": metrics,
            "events": events.history(),
            "recommendations": recommendations,
        }
