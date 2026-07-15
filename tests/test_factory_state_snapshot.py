from ai.factory.state_snapshot import (
    FactoryStateSnapshot,
)


def test_snapshot_creation():
    snapshot = FactoryStateSnapshot()

    result = snapshot.create(
        ["project-1"],
        ["task-1"],
        ["artifact-1"],
        {
            "tasks_total": 1,
        },
        {
            "status": "HEALTHY",
        },
    )

    assert "timestamp" in result
    assert result["projects"][0] == "project-1"
    assert result["metrics"]["tasks_total"] == 1
    assert result["health"]["status"] == "HEALTHY"


def test_snapshot_contains_collections():
    snapshot = FactoryStateSnapshot()

    result = snapshot.create(
        [],
        [],
        [],
        {},
        {},
    )

    assert result["projects"] == []
    assert result["tasks"] == []
    assert result["artifacts"] == []
