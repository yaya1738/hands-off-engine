from ai.factory.ide_controller import (
    FactoryIDEController,
)


class FakeControlPlane:
    def inspect(self):
        return {
            "health": "OK",
        }

    def optimize(self):
        return {
            "action": "continue",
        }

    def latest_state(self):
        return {
            "version": 1,
        }


class FakeWorkspace:
    def __init__(self):
        self.projects = {}

    def create_project(
        self,
        project_id,
        name,
    ):
        self.projects[project_id] = name


def test_inspect():
    controller = FactoryIDEController(
        FakeControlPlane(),
        FakeWorkspace(),
    )

    result = controller.inspect()

    assert result["health"] == "OK"


def test_create_project():
    workspace = FakeWorkspace()

    controller = FactoryIDEController(
        FakeControlPlane(),
        workspace,
    )

    result = controller.create_project(
        "p1",
        "Factory Project",
    )

    assert result["status"] == "CREATED"
    assert workspace.projects["p1"] == "Factory Project"


def test_optimize():
    controller = FactoryIDEController(
        FakeControlPlane(),
        FakeWorkspace(),
    )

    result = controller.optimize()

    assert result["action"] == "continue"
