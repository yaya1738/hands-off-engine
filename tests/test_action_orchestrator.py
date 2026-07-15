from ai.factory.action_orchestrator import (
    FactoryActionOrchestrator,
)


def build():
    return FactoryActionOrchestrator()


def test_register_action():
    orchestrator = build()

    result = orchestrator.register_action(
        {
            "action": "RUN",
        }
    )

    assert result["registered"] is True


def test_sequence():
    orchestrator = build()

    orchestrator.register_action({})

    result = orchestrator.sequence()

    assert len(result["sequence"]) == 1


def test_coordinate():
    orchestrator = build()

    result = orchestrator.coordinate()

    assert result["coordinated"] is True


def test_monitor():
    orchestrator = build()

    result = orchestrator.monitor()

    assert result["monitored"] is True


def test_history():
    orchestrator = build()

    orchestrator.register_action({})

    assert len(orchestrator.history()) == 1
