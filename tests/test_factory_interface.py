from ai.factory.interface import FactoryInterface


class FakeController:
    def __init__(self):
        self.memory = FakeMemory()

    def build(self, task_id, goal):
        return {
            "task_id": task_id,
            "goal": goal,
        }


class FakeMemory:
    def recall_all(self):
        return [
            {
                "task_id": "1",
            }
        ]


def test_interface_run():
    interface = FactoryInterface(
        FakeController()
    )

    result = interface.run_task(
        "task-1",
        "test build",
    )

    assert result["task_id"] == "task-1"


def test_interface_status():
    interface = FactoryInterface(
        FakeController()
    )

    result = interface.status()

    assert result["factory"] == "active"
    assert result["memory_records"] == 1
