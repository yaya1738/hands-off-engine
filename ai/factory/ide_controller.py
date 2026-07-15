from typing import Any


class FactoryIDEController:
    def __init__(
        self,
        control_plane: Any,
        workspace: Any,
    ):
        self.control_plane = control_plane
        self.workspace = workspace

    def inspect(self):
        return self.control_plane.inspect()

    def create_project(
        self,
        project_id: str,
        name: str,
    ):
        self.workspace.create_project(
            project_id,
            name,
        )

        return {
            "status": "CREATED",
            "project_id": project_id,
        }

    def optimize(self):
        return self.control_plane.optimize()

    def latest_state(self):
        return self.control_plane.latest_state()
