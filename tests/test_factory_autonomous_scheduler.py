from pathlib import Path

from ai.factory.autonomous_scheduler import FactoryAutonomousScheduler


class FakeAuthority:
    def __init__(self):
        self.objectives = []

    def execute_autonomous(self, objective):
        self.objectives.append(objective)
        return {"status": "completed", "objective": objective}


def test_scheduler_persists_queue_and_routes_through_authority(tmp_path: Path):
    state_file = tmp_path / "scheduler.json"
    authority = FakeAuthority()

    scheduler = FactoryAutonomousScheduler(authority=authority, state_file=state_file)
    queued = scheduler.schedule_task({"objective": "inspect factory health", "capability": "health"})

    assert queued["scheduled"] is True
    assert queued["task"]["status"] == "pending"
    assert state_file.exists()

    result = scheduler.run_cycle()

    assert result["executed"] is True
    assert authority.objectives == ["inspect factory health"]
    assert result["task"]["status"] == "completed"

    restarted = FactoryAutonomousScheduler(
        authority=FakeAuthority(),
        state_file=state_file,
    )
    assert restarted.tasks[0]["status"] == "completed"
    assert restarted.history()


def test_scheduler_rejects_empty_objective(tmp_path: Path):
    scheduler = FactoryAutonomousScheduler(
        authority=FakeAuthority(),
        state_file=tmp_path / "scheduler.json",
    )

    try:
        scheduler.schedule_task({"objective": "  "})
    except ValueError as exc:
        assert "objective" in str(exc)
    else:
        raise AssertionError("empty objectives must be rejected")
