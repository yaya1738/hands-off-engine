from ai.factory.control_plane import (
    FactoryControlPlane,
)


class FakeScheduler:
    def run_pending(self):
        return {
            "status": "DONE",
        }


class FakeSupervisor:
    def monitor(self, data):
        return {
            "healthy": True,
        }


class FakeRecovery:
    def restore(self):
        return {
            "status": "RESTORED",
        }


class FakeOrchestrator:
    def run(self, state):
        return {
            "cycle": True,
        }


def build():
    return FactoryControlPlane(
        scheduler=FakeScheduler(),
        supervisor=FakeSupervisor(),
        recovery=FakeRecovery(),
        orchestrator=FakeOrchestrator(),
    )


def test_start():
    plane = build()

    result = plane.start()

    assert result["status"] == "STARTED"


def test_cycle():
    plane = build()

    result = plane.cycle({})

    assert result["health"]["healthy"] is True


def test_recover():
    plane = build()

    result = plane.recover()

    assert result["status"] == "RESTORED"


def test_history():
    plane = build()

    plane.start()

    assert len(plane.history()) == 1
