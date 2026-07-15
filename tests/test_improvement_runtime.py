from ai.factory.improvement_runtime import (
    FactoryImprovementRuntime,
)


class FakeOrchestrator:
    def __init__(self):
        self.calls = 0

    def run_cycle(self, metrics):
        self.calls += 1

        return {
            "cycle": self.calls,
            "metrics": metrics,
        }


def test_run_once():
    runtime = FactoryImprovementRuntime(
        FakeOrchestrator()
    )

    result = runtime.run_once(
        {
            "success_rate": 1,
        }
    )

    assert result["cycle"] == 1


def test_start():
    runtime = FactoryImprovementRuntime(
        FakeOrchestrator()
    )

    runtime.start(
        {
            "success_rate": 1,
        }
    )

    assert runtime.running is True


def test_stop():
    runtime = FactoryImprovementRuntime(
        FakeOrchestrator()
    )

    result = runtime.stop()

    assert result["status"] == "STOPPED"


def test_history():
    runtime = FactoryImprovementRuntime(
        FakeOrchestrator()
    )

    runtime.run_once({})

    assert len(runtime.history()) == 1
