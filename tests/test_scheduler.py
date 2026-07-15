from ai.factory.scheduler import (
    FactoryScheduler,
)


def build():
    return FactoryScheduler()


def test_schedule_task():
    scheduler = build()

    result = scheduler.schedule_task(
        {
            "task": "RUN",
        }
    )

    assert result["scheduled"] is True


def test_cancel_task():
    scheduler = build()

    result = scheduler.cancel_task(
        {}
    )

    assert result["cancelled"] is True


def test_run_due_tasks():
    scheduler = build()

    result = scheduler.run_due_tasks()

    assert result["executed"] is True


def test_check_schedule():
    scheduler = build()

    result = scheduler.check_schedule()

    assert result["checked"] is True


def test_history():
    scheduler = build()

    scheduler.schedule_task({})

    assert len(scheduler.history()) == 1
