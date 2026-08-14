from scripts import autonomous_daemon


def test_factory_owned_work_is_dispatched_through_persistent_scheduler(monkeypatch):
    calls = []

    class FakeScheduler:
        def __init__(self):
            calls.append("init")

        def schedule_task(self, task):
            calls.append(("schedule", task))
            return {"scheduled": True}

        def run_cycle(self):
            calls.append("run_cycle")
            return {"executed": False}

    monkeypatch.setattr(autonomous_daemon, "FactoryAutonomousScheduler", FakeScheduler)

    assert autonomous_daemon.task_self_improvement() is True
    assert autonomous_daemon.task_factory_scheduler() is True
    assert [call[0] if isinstance(call, tuple) else call for call in calls] == [
        "init", "schedule", "init", "run_cycle"
    ]


def test_trading_task_remains_hard_blocked(monkeypatch):
    launched = []

    monkeypatch.setattr(autonomous_daemon, "run_subprocess", lambda *args, **kwargs: launched.append(args) or (True, ""))

    assert autonomous_daemon.LIVE_TRADING_ENABLED is False
    assert autonomous_daemon.task_trading_pipeline() is False
    assert launched == []
