from types import SimpleNamespace

from ai.factory.persistence import FactoryPersistence


class FakeRegistry:
    def list_components(self):
        return [
            "planner",
            "runner",
        ]


class FakeRuntime:
    registry = FakeRegistry()

    def status(self):
        return {
            "status": "HEALTHY",
        }


def test_save_runtime():
    persistence = FactoryPersistence()

    snapshot = persistence.save_runtime(
        FakeRuntime()
    )

    assert "planner" in snapshot["components"]
    assert snapshot["health"]["status"] == "HEALTHY"


def test_restore_runtime():
    persistence = FactoryPersistence()

    result = persistence.restore_runtime(
        {
            "components": ["planner"],
            "health": {
                "status": "HEALTHY",
            },
        }
    )

    assert result["restored"] is True
    assert "planner" in result["components"]
