from ai.factory.daemon_scheduler import (
    FactoryDaemonScheduler,
)


class FakeDaemon:
    def __init__(self, running=True):
        self.running = running

    def status(self):
        return {
            "running": self.running,
        }


class FakeScheduler:
    def run_pending(self):
        return [
            {
                "job_id": "job-1",
            }
        ]

    def list_jobs(self):
        return [
            {
                "job_id": "job-1",
            }
        ]


def test_run_cycle():
    manager = FactoryDaemonScheduler(
        FakeDaemon(True),
        FakeScheduler(),
    )

    result = manager.run_cycle()

    assert result["status"] == "active"
    assert result["jobs"][0]["job_id"] == "job-1"


def test_inactive_daemon():
    manager = FactoryDaemonScheduler(
        FakeDaemon(False),
        FakeScheduler(),
    )

    result = manager.tick()

    assert result["status"] == "inactive"


def test_status():
    manager = FactoryDaemonScheduler(
        FakeDaemon(True),
        FakeScheduler(),
    )

    result = manager.status()

    assert result["daemon"]["running"] is True
    assert len(result["jobs"]) == 1
