from ai.factory.workspace import FactoryWorkspace


def test_create_project():
    workspace = FactoryWorkspace()

    workspace.create_project(
        "proj-001",
        "Audit System",
    )

    assert "proj-001" in workspace.list_projects()


def test_add_task():
    workspace = FactoryWorkspace()

    workspace.create_project(
        "proj-001",
        "Factory",
    )

    workspace.add_task(
        "proj-001",
        {
            "id": "task-1",
        },
    )

    project = workspace.get_project(
        "proj-001"
    )

    assert len(project["tasks"]) == 1


def test_add_artifact():
    workspace = FactoryWorkspace()

    workspace.create_project(
        "proj-001",
        "Factory",
    )

    workspace.add_artifact(
        "proj-001",
        {
            "file": "module.py",
        },
    )

    project = workspace.get_project(
        "proj-001"
    )

    assert project["artifacts"][0]["file"] == "module.py"
