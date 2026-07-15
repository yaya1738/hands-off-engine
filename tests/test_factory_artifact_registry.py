from ai.factory.artifact_registry import FactoryArtifactRegistry


def test_register_artifact():
    registry = FactoryArtifactRegistry()

    registry.register_artifact(
        "artifact-001",
        "task-001",
        "code",
        "ai/factory/test.py",
    )

    result = registry.get_artifact(
        "artifact-001"
    )

    assert result["type"] == "code"
    assert result["status"] == "CREATED"


def test_find_artifacts_by_task():
    registry = FactoryArtifactRegistry()

    registry.register_artifact(
        "artifact-002",
        "task-002",
        "report",
        "report.json",
    )

    results = registry.find_by_task(
        "task-002"
    )

    assert len(results) == 1


def test_list_artifacts():
    registry = FactoryArtifactRegistry()

    assert registry.list_artifacts() == []
