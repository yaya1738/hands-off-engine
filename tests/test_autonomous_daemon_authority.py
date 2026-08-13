"""Regression tests for daemon-to-Factory authority routing."""


def test_self_improvement_uses_factory_scheduler(monkeypatch):
    import scripts.autonomous_daemon as daemon

    calls = []

    class FakeScheduler:
        def run_self_improvement(self):
            calls.append("factory")
            return {"success": True}

    monkeypatch.setattr(daemon, "FactoryAutonomousScheduler", FakeScheduler)

    assert daemon.task_self_improvement() is True
    assert calls == ["factory"]
