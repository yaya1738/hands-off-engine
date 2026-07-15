from ai.factory.runtime_coordinator import (
    FactoryRuntimeCoordinator,
)


class FakeLifecycle:
    def startup(self):
        return {
            "status": "started",
        }

    def shutdown(self, state):
        return {
            "status": "stopped",
        }


class FakeScheduler:
    def tick(self):
        return {
            "status": "active",
        }

    def status(self):
        return {
            "running": True,
        }


class FakePublisher:
    def publish(self):
        return {
            "health": "HEALTHY",
        }


def test_initialize():
    coordinator = FactoryRuntimeCoordinator(
        FakeLifecycle(),
        FakeScheduler(),
    )

    result = coordinator.initialize()

    assert result["status"] == "started"


def test_run_cycle():
    coordinator = FactoryRuntimeCoordinator(
        FakeLifecycle(),
        FakeScheduler(),
        FakePublisher(),
    )

    result = coordinator.run_cycle()

    assert result["status"] == "active"
    assert result["snapshot"]["health"] == "HEALTHY"


def test_status():
    coordinator = FactoryRuntimeCoordinator(
        FakeLifecycle(),
        FakeScheduler(),
    )

    assert coordinator.status()["running"] is True
