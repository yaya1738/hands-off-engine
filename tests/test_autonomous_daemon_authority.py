"""Regression tests for daemon-to-Factory authority routing."""


def test_self_improvement_uses_factory_scheduler(monkeypatch):
    import scripts.autonomous_daemon as daemon

    calls = []

    class FakeScheduler:
        def __init__(self):
            calls.append("init")

        def schedule_task(self, task):
            calls.append(("schedule", task))
            return {"scheduled": True}

    monkeypatch.setattr(daemon, "FactoryAutonomousScheduler", FakeScheduler)

    assert daemon.task_self_improvement() is True
    assert [call[0] if isinstance(call, tuple) else call for call in calls] == [
        "init", "schedule"
    ]
