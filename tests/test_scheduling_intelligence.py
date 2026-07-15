from ai.factory.scheduling_intelligence import (
    FactorySchedulingIntelligence,
)


def build():
    return FactorySchedulingIntelligence()


def test_create_schedule():
    engine = build()

    result = engine.create_schedule(
        {}
    )

    assert result["created"] is True


def test_queue_task():
    engine = build()

    result = engine.queue_task(
        {}
    )

    assert result["queued"] is True


def test_execute_due_tasks():
    engine = build()

    result = engine.execute_due_tasks()

    assert result["executed"] is True


def test_prioritize_tasks():
    engine = build()

    result = engine.prioritize_tasks(
        []
    )

    assert result["prioritized"] is True


def test_history():
    engine = build()

    engine.queue_task(
        {}
    )

    assert len(engine.history()) == 1
