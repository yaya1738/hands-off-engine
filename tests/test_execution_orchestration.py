from ai.factory.execution_orchestration import (
    FactoryExecutionOrchestration,
)


def build():
    return FactoryExecutionOrchestration()


def test_start_execution():
    engine = build()

    result = engine.start_execution(
        {
            "goal": "RUN",
        }
    )

    assert result["status"] == "STARTED"


def test_coordinate_tasks():
    engine = build()

    result = engine.coordinate_tasks(
        [
            {
                "task": 1,
            }
        ]
    )

    assert result["coordinated"] is True


def test_monitor_execution():
    engine = build()

    result = engine.monitor_execution(
        {}
    )

    assert result["monitored"] is True


def test_recover_failure():
    engine = build()

    result = engine.recover_failure(
        {}
    )

    assert result["recovered"] is True


def test_history():
    engine = build()

    engine.start_execution({})

    assert len(engine.history()) == 1
