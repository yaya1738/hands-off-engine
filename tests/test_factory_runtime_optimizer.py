from ai.factory.runtime_optimizer import FactoryRuntimeOptimizer


class FakeMemory:
    def recall_all(self):
        return [
            {
                "event": "test",
            }
        ]


class FakeController:
    memory = FakeMemory()


class FakeRuntime:
    controller = FakeController()

    def status(self):
        return {
            "status": "HEALTHY",
        }


class FakeOptimizer:
    def run_cycle(
        self,
        health,
        history,
        telemetry,
    ):
        return {
            "health": health,
            "history_count": len(history),
        }


def test_runtime_optimizer_cycle():
    manager = FactoryRuntimeOptimizer(
        FakeRuntime(),
        FakeOptimizer(),
    )

    result = manager.optimize()

    assert result["health"]["status"] == "HEALTHY"
    assert result["history_count"] == 1
