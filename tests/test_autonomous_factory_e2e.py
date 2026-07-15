from ai.factory.control_plane import (
    FactoryControlPlane,
)


class FakeScheduler:
    def __init__(self):
        self.executed = False

    def run_pending(self):
        self.executed = True

        return {
            "status": "DONE",
        }


class FakeSupervisor:
    def monitor(self, components):
        return {
            "healthy": True,
        }


class FakeRecovery:
    def restore(self):
        return {
            "status": "RESTORED",
        }


class FakeOrchestrator:
    def __init__(self):
        self.runs = 0

    def run(self, state):
        self.runs += 1

        return {
            "cycle": "COMPLETE",
        }


def build_factory():
    return FactoryControlPlane(
        scheduler=FakeScheduler(),
        supervisor=FakeSupervisor(),
        recovery=FakeRecovery(),
        orchestrator=FakeOrchestrator(),
    )


def test_startup_flow():
    factory = build_factory()

    result = factory.start()

    assert result["status"] == "STARTED"


def test_operational_cycle():
    factory = build_factory()

    result = factory.cycle(
        {
            "mode": "AUTO",
        }
    )

    assert (
        result["orchestration"]["cycle"]
        == "COMPLETE"
    )


def test_recovery_flow():
    factory = build_factory()

    result = factory.recover()

    assert result["status"] == "RESTORED"


def test_full_autonomous_loop():
    factory = build_factory()

    factory.start()

    result = factory.cycle({})

    assert (
        result["health"]["healthy"]
        is True
    )

    assert (
        result["schedule"]["status"]
        == "DONE"
    )


def test_history():
    factory = build_factory()

    factory.start()
    factory.cycle({})

    assert len(factory.history()) == 2
