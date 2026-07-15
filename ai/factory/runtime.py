from ai.factory.controller import FactoryController
from ai.factory.registry import FactoryRegistry
from ai.factory.health import FactoryHealth
from ai.factory.dashboard import FactoryDashboard


class FactoryRuntime:
    def __init__(self):
        self.controller = FactoryController()
        self.registry = FactoryRegistry()
        self.health = FactoryHealth()
        self.dashboard = FactoryDashboard()

        self._register_components()

    def _register_components(self):
        self.registry.register("planner", "planning")
        self.registry.register("runner", "execution")
        self.registry.register("verifier", "validation")
        self.registry.register("memory", "learning")

    def status(self):
        return self.health.check(
            registry=self.registry,
            memory=self.controller.memory,
            state={},
        )

    def view(self):
        return self.dashboard.snapshot(
            health=self.status(),
            registry=self.registry.list_components(),
            telemetry={},
            state={},
        )

    def run(self, task_id: str, goal: str):
        return self.controller.build(
            task_id,
            goal,
        )
