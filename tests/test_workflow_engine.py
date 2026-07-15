from ai.factory.workflow_engine import (
    FactoryWorkflowEngine,
)


def build():
    return FactoryWorkflowEngine()


def test_create_workflow():
    engine = build()

    result = engine.create_workflow(
        "startup",
        {}
    )

    assert result["created"] is True


def test_add_step():
    engine = build()

    result = engine.add_step(
        "startup",
        {
            "action": "RUN",
        }
    )

    assert result["added"] is True


def test_execute_workflow():
    engine = build()

    result = engine.execute_workflow(
        "startup"
    )

    assert result["executed"] is True


def test_validate_workflow():
    engine = build()

    result = engine.validate_workflow(
        "startup"
    )

    assert result["validated"] is True


def test_history():
    engine = build()

    engine.create_workflow(
        "x",
        {}
    )

    assert len(engine.history()) == 1
