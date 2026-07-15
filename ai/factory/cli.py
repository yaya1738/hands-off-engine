from ai.factory.controller import FactoryController
from ai.factory.interface import FactoryInterface


class FactoryCLI:
    def __init__(self):
        controller = FactoryController()
        self.interface = FactoryInterface(controller)

    def status(self):
        return self.interface.status()

    def run(self, task_id: str, goal: str):
        return self.interface.run_task(
            task_id,
            goal,
        )

    def history(self):
        return self.interface.history()
