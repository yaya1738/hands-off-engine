from ai.factory.planner import FactoryPlanner
from ai.factory.runner import FactoryRunner
from ai.factory.verifier import FactoryVerifier
from ai.factory.memory import FactoryMemory


class FactoryController:
    def __init__(self):
        self.planner = FactoryPlanner()
        self.runner = FactoryRunner()
        self.verifier = FactoryVerifier()
        self.memory = FactoryMemory()

    def build(self, task_id: str, goal: str):
        plan = self.planner.plan(
            {
                "goal": goal,
            }
        )

        execution = self.runner.run(
            task_id,
            plan,
        )

        verification = self.verifier.verify(
            execution
        )

        result = {
            "task_id": task_id,
            "plan": plan,
            "execution": execution,
            "verification": verification,
        }

        self.memory.remember(
            {
                "task_id": task_id,
                "status": execution.status,
                "valid": verification["valid"],
            }
        )

        return result
