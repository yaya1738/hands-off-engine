from ai.factory.master_orchestrator import (
    FactoryMasterOrchestrator,
)


class FakeControl:
    def start(self):
        return {
            "status": "STARTED",
        }


class FakeLoop:
    def run_cycle(self, state):
        return {
            "decision": {
                "decision": "CONTINUE",
            },
            "action": {
                "status": "OK",
            },
        }


class FakeEvolution:
    def evolve(self, metrics):
        return {
            "upgrade": {
                "action": "OPTIMIZE",
            },
        }


def build_system():
    return FactoryMasterOrchestrator(
        control_plane=FakeControl(),
        loop=FakeLoop(),
        evolution=FakeEvolution(),
    )


def test_full_cycle():
    factory = build_system()

    factory.start()

    result = factory.run(
        {
            "success_rate": 1,
        }
    )

    assert (
        result["cycle"]["action"]["status"]
        == "OK"
    )


def test_learning_path():
    factory = build_system()

    result = factory.run(
        {
            "success_rate": 0.5,
        }
    )

    assert (
        result["evolution"]["upgrade"]["action"]
        == "OPTIMIZE"
    )


def test_startup():
    factory = build_system()

    result = factory.start()

    assert result["status"] == "STARTED"


def test_history():
    factory = build_system()

    factory.start()

    assert len(factory.history()) == 1
