from ai.factory.job_runner import (
    FactoryJobRunner,
)


class FakeExecutor:
    def execute(
        self,
        job_type,
        payload=None,
    ):
        return {
            "executed": job_type,
        }


def test_run_job():
    runner = FactoryJobRunner(
        FakeExecutor()
    )

    result = runner.run_job(
        "snapshot"
    )

    assert result["result"]["executed"] == "snapshot"


def test_run_cycle():
    runner = FactoryJobRunner(
        FakeExecutor()
    )

    result = runner.run_cycle(
        [
            {
                "action": "health",
            },
            {
                "action": "optimize",
            },
        ]
    )

    assert len(result) == 2


def test_history():
    runner = FactoryJobRunner(
        FakeExecutor()
    )

    runner.run_job(
        "snapshot"
    )

    assert len(runner.history()) == 1
