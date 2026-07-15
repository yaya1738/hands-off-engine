from ai.factory.autonomous_scheduler import (
    FactoryAutonomousScheduler,
)


def build():
    return FactoryAutonomousScheduler()


def test_schedule_task():
    scheduler = build()

    result = scheduler.schedule_task(
        {
            "task": "OPTIMIZE",
        }
    )

    assert result["scheduled"] is True


def test_run_cycle():
    scheduler = build()

    result = scheduler.run_cycle()

    assert result["cycle_run"] is True


def test_prioritize_schedule():
    scheduler = build()

    scheduler.schedule_task(
        {
            "id": 1,
        }
    )

    result = scheduler.prioritize_schedule()

    assert result["priority_task"]["id"] == 1


def test_history():
    scheduler = build()

    scheduler.run_cycle()

    assert len(scheduler.history()) == 1
