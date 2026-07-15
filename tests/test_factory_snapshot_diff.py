from ai.factory.snapshot_diff import (
    FactorySnapshotDiff,
)


def test_snapshot_compare():
    diff_engine = FactorySnapshotDiff()

    result = diff_engine.compare(
        {
            "tasks": 10,
            "artifacts": 5,
        },
        {
            "tasks": 12,
            "artifacts": 7,
        },
    )

    assert "tasks" in result
    assert result["tasks"]["before"] == 10
    assert result["tasks"]["after"] == 12


def test_changed_fields():
    diff_engine = FactorySnapshotDiff()

    diff = diff_engine.compare(
        {
            "status": "OLD",
        },
        {
            "status": "NEW",
        },
    )

    fields = diff_engine.changed_fields(
        diff
    )

    assert "status" in fields


def test_summary():
    diff_engine = FactorySnapshotDiff()

    summary = diff_engine.summarize(
        {
            "one": {},
            "two": {},
        }
    )

    assert summary["changed_count"] == 2
