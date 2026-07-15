from ai.factory.api import FactoryAPI


class FakeMemory:
    def recall_all(self):
        return [
            {
                "task_id": "1",
            }
        ]


class FakeController:
    memory = FakeMemory()


class FakeRuntime:
    controller = FakeController()

    def status(self):
        return {
            "status": "HEALTHY",
        }

    def view(self):
        return {
            "health": {
                "status": "HEALTHY",
            }
        }

    def run(self, task_id, goal):
        return {
            "task_id": task_id,
            "goal": goal,
        }


def test_api_status():
    api = FactoryAPI(FakeRuntime())

    assert api.status()["status"] == "HEALTHY"


def test_api_run():
    api = FactoryAPI(FakeRuntime())

    result = api.run_task(
        "api-001",
        "test api",
    )

    assert result["task_id"] == "api-001"


def test_api_history():
    api = FactoryAPI(FakeRuntime())

    assert len(api.history()) == 1
