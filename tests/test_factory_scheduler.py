from ai.factory.scheduler import (
    FactoryScheduler,
)


def test_schedule_job():
    scheduler = FactoryScheduler()

    scheduler.schedule(
        "job-001",
        "optimize",
        60,
    )

    jobs = scheduler.list_jobs()

    assert jobs[0]["action"] == "optimize"
    assert jobs[0]["status"] == "SCHEDULED"


def test_run_pending():
    scheduler = FactoryScheduler()

    scheduler.schedule(
        "job-002",
        "snapshot",
        30,
    )

    result = scheduler.run_pending()

    assert result[0]["action"] == "snapshot"
    assert scheduler.list_jobs()[0]["runs"] == 1
    assert scheduler.list_jobs()[0]["status"] == "COMPLETE"


def test_empty_scheduler():
    scheduler = FactoryScheduler()

    assert scheduler.run_pending() == []
