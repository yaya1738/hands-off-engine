from typing import Any


class FactoryAPI:
    def __init__(self, runtime: Any):
        self.runtime = runtime

    def status(self):
        return self.runtime.status()

    def dashboard(self):
        return self.runtime.view()

    def run_task(self, task_id: str, goal: str):
        return self.runtime.run(
            task_id,
            goal,
        )

    def history(self):
        return self.runtime.controller.memory.recall_all()
