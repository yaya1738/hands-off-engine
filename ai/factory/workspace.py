from typing import Any, Dict, List


class FactoryWorkspace:
    def __init__(self):
        self._projects: Dict[str, Dict[str, Any]] = {}

    def create_project(
        self,
        project_id: str,
        name: str,
    ) -> None:
        self._projects[project_id] = {
            "name": name,
            "tasks": [],
            "artifacts": [],
        }

    def add_task(
        self,
        project_id: str,
        task: Dict[str, Any],
    ) -> None:
        self._projects[project_id]["tasks"].append(task)

    def add_artifact(
        self,
        project_id: str,
        artifact: Dict[str, Any],
    ) -> None:
        self._projects[project_id]["artifacts"].append(
            artifact
        )

    def list_projects(self) -> List[str]:
        return list(self._projects.keys())

    def get_project(
        self,
        project_id: str,
    ):
        return self._projects.get(project_id)
