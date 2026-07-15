from ai.factory.master_orchestrator import (
    FactoryMasterOrchestrator,
)


class FakeControl:
    def start(self):
        return True


class FakeLoop:
    def run_cycle(self, state):
        return {
            "cycle": 1,
        }


class FakeEvolution:
    def evolve(self, state):
        return {
            "evolved": True,
        }


def build():
    return FactoryMasterOrchestrator(
        control_plane=FakeControl(),
        loop=FakeLoop(),
        evolution=FakeEvolution(),
    )


def test_start():
    orchestrator = build()

    result = orchestrator.start()

    assert result["status"] == "STARTED"


def test_run():
    orchestrator = build()

    result = orchestrator.run({})

    assert result["cycle"]["cycle"] == 1


def test_status():
    orchestrator = build()

    orchestrator.start()

    assert orchestrator.status()["running"] is True


def test_history():
    orchestrator = build()

    orchestrator.start()

    assert len(orchestrator.history()) == 1
