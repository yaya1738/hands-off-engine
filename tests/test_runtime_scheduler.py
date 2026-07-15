from ai.factory.runtime_scheduler import (
    FactoryRuntimeScheduler,
)


def test_schedule():
    scheduler = FactoryRuntimeScheduler()

    job = scheduler.schedule(
        "cycle",
        lambda: "done",
    )

    assert job["status"] == "SCHEDULED"


def test_run():
    scheduler = FactoryRuntimeScheduler()

    scheduler.schedule(
        "cycle",
        lambda: "done",
    )

    result = scheduler.run()

    assert result[0]["result"] == "done"


def test_cancel():
    scheduler = FactoryRuntimeScheduler()

    job = scheduler.schedule(
        "cycle",
        lambda: "done",
    )

    result = scheduler.cancel(
        "cycle"
    )

    assert result["status"] == "CANCELLED"


def test_history():
    scheduler = FactoryRuntimeScheduler()

    scheduler.schedule(
        "cycle",
        lambda: "done",
    )

    scheduler.run()

    assert len(scheduler.history()) == 1
