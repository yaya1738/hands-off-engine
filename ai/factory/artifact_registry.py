from typing import Any, Dict, List


class FactoryArtifactRegistry:
    def __init__(self):
        self._artifacts: List[Dict[str, Any]] = []

    def register_artifact(
        self,
        artifact_id: str,
        task_id: str,
        artifact_type: str,
        location: str,
        approval_id=None,
    ) -> None:
        artifact = {
            "artifact_id": artifact_id,
            "task_id": task_id,
            "type": artifact_type,
            "location": location,
            "status": "CREATED",
        }

        if approval_id:
            artifact["approval_id"] = approval_id

        self._artifacts.append(artifact)



    def update_artifact(
        self,
        artifact_id: str,
        updates: Dict[str, Any],
    ):
        for artifact in self._artifacts:
            if artifact["artifact_id"] == artifact_id:
                artifact.update(updates)
                return artifact

        return None


    def complete_artifact(
        self,
        artifact_id: str,
        outcome: Dict[str, Any],
    ):
        return self.update_artifact(
            artifact_id,
            {
                "status": "COMPLETED",
                "outcome": outcome,
            },
        )

    def get_artifact(
        self,
        artifact_id: str,
    ):
        for artifact in self._artifacts:
            if artifact["artifact_id"] == artifact_id:
                return artifact

        return None

    def list_artifacts(self):
        return self._artifacts

    def find_by_task(
        self,
        task_id: str,
    ):
        return [
            artifact
            for artifact in self._artifacts
            if artifact["task_id"] == task_id
        ]
