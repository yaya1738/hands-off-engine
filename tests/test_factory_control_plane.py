from ai.factory.control_plane import (
    FactoryControlPlane,
)


class FakeRuntime:
    def status(self):
        return {
            "status": "HEALTHY",
        }

    def view(self):
        return {
            "view": True,
        }


class FakeStore:
    def __init__(self):
        self.value = None

    def save_snapshot(self, snapshot):
        self.value = snapshot

    def get_latest(self):
        return self.value


class FakeDiff:
    def compare(self, before, after):
        return {
            "changed": True,
        }


class FakeOptimizer:
    def optimize(self):
        return {
            "action": "continue",
        }


def test_control_plane_inspect():
    plane = FactoryControlPlane(
        FakeRuntime(),
        FakeStore(),
        FakeDiff(),
        FakeOptimizer(),
    )

    result = plane.inspect()

    assert result["health"]["status"] == "HEALTHY"


def test_control_plane_snapshot():
    plane = FactoryControlPlane(
        FakeRuntime(),
        FakeStore(),
        FakeDiff(),
        FakeOptimizer(),
    )

    plane.save_state(
        {
            "version": 1,
        }
    )

    assert plane.latest_state()["version"] == 1


def test_control_plane_optimize():
    plane = FactoryControlPlane(
        FakeRuntime(),
        FakeStore(),
        FakeDiff(),
        FakeOptimizer(),
    )

    assert plane.optimize()["action"] == "continue"
