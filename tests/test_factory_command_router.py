from ai.factory.command_router import FactoryCommandRouter


class FakeAPI:
    def status(self):
        return {
            "status": "HEALTHY",
        }

    def dashboard(self):
        return {
            "dashboard": True,
        }

    def run_task(self, task_id, goal):
        return {
            "task_id": task_id,
            "goal": goal,
        }

    def history(self):
        return [
            "event",
        ]


def test_status_command():
    router = FactoryCommandRouter(
        FakeAPI()
    )

    result = router.dispatch(
        "status",
        {},
    )

    assert result["status"] == "HEALTHY"


def test_run_task_command():
    router = FactoryCommandRouter(
        FakeAPI()
    )

    result = router.dispatch(
        "run_task",
        {
            "task_id": "001",
            "goal": "test router",
        },
    )

    assert result["task_id"] == "001"


def test_unknown_command():
    router = FactoryCommandRouter(
        FakeAPI()
    )

    result = router.dispatch(
        "unknown",
        {},
    )

    assert result["error"] == "unknown_command"
