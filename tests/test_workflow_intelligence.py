from ai.factory.workflow_intelligence import (
    FactoryWorkflowIntelligence,
)


def build():
    return FactoryWorkflowIntelligence()


def test_create_workflow():
    engine = build()

    result = engine.create_workflow(
        "test",
        {}
    )

    assert result["created"] is True


def test_add_step():
    engine = build()

    result = engine.add_step(
        "test",
        {}
    )

    assert result["added"] is True


def test_execute_workflow():
    engine = build()

    result = engine.execute_workflow(
        "test"
    )

    assert result["executed"] is True


def test_track_progress():
    engine = build()

    result = engine.track_progress(
        "test"
    )

    assert result["tracked"] is True


def test_history():
    engine = build()

    engine.create_workflow(
        "x",
        {}
    )

    assert len(engine.history()) == 1
