from ai.factory.runtime_scheduler import (
    FactoryRuntimeScheduler,
)


def fake_executor(task):
    return {
        "executed": task,
    }


def build():
    return FactoryRuntimeScheduler(
        executor=fake_executor
    )


def test_schedule():
    scheduler = build()

    result = scheduler.schedule(
        {
            "name": "cycle",
        }
    )

    assert result["status"] == "SCHEDULED"


def test_run_pending():
    scheduler = build()

    scheduler.schedule(
        {
            "name": "cycle",
        }
    )

    result = scheduler.run_pending()

    assert result["status"] == "COMPLETED"


def test_pause():
    scheduler = build()

    result = scheduler.pause()

    assert result["status"] == "PAUSED"


def test_history():
    scheduler = build()

    scheduler.schedule({})

    assert len(scheduler.history()) == 1
