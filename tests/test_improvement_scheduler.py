from ai.factory.improvement_scheduler import (
    FactoryImprovementScheduler,
)


def test_schedule():
    scheduler = FactoryImprovementScheduler()

    job = scheduler.schedule(
        "test",
        lambda: "done",
    )

    assert job["name"] == "test"


def test_run_cycle():
    scheduler = FactoryImprovementScheduler()

    scheduler.schedule(
        "test",
        lambda: "done",
    )

    result = scheduler.run_cycle()

    assert result[0]["result"] == "done"


def test_multiple_jobs():
    scheduler = FactoryImprovementScheduler()

    scheduler.schedule(
        "a",
        lambda: 1,
    )

    scheduler.schedule(
        "b",
        lambda: 2,
    )

    result = scheduler.run_cycle()

    assert len(result) == 2


def test_history():
    scheduler = FactoryImprovementScheduler()

    scheduler.schedule(
        "test",
        lambda: "done",
    )

    scheduler.run_cycle()

    assert len(scheduler.history()) == 1
