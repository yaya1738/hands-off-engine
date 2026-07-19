from datetime import datetime, timezone
from typing import Any, Dict, List
import uuid


class FactoryDevelopmentArtifactGenerator:

    def __init__(self):
        self._artifacts: List[Dict[str, Any]] = []

    def generate(
        self,
        objective: str,
        plan: Dict[str, Any],
        context: Dict[str, Any] = None,
    ):
        artifact = {
            "artifact_id": str(uuid.uuid4()),
            "type": "development_proposal",
            "objective": objective,
            "plan": plan,
            "context": context or {},
            "task_id": context.get("task_id") if context else None,
            "location": "factory_generated_proposals",
            "status": "PROPOSED",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "validation_required": True,
        }

        self._artifacts.append(
            artifact
        )

        return artifact

    def history(self):
        return self._artifacts
