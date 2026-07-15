from typing import Any


class FactoryInterface:
    def __init__(self, controller: Any):
        self.controller = controller

    def run_task(self, task_id: str, goal: str):
        return self.controller.build(
            task_id,
            goal,
        )

    def history(self):
        return self.controller.memory.recall_all()

    def status(self):
        return {
            "factory": "active",
            "memory_records": len(
                self.controller.memory.recall_all()
            ),
        }
