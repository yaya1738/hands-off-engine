from typing import Any, Dict, List


class FactoryImprovementOrchestrator:
    def __init__(
        self,
        assessor=None,
        planner=None,
        queue=None,
    ):
        self.assessor = assessor
        self.planner = planner
        self.queue = queue
        self._history: List[Dict[str, Any]] = []

    def run_cycle(
        self,
        metrics: Dict[str, Any],
    ):
        assessment = self.assessor.assess(
            metrics
        )

        plan = self.planner.plan(
            assessment
        )

        queued = []

        for task in plan.get(
            "tasks",
            [],
        ):
            queued.append(
                self.queue.enqueue(
                    {
                        "name": task,
                        "priority": plan.get(
                            "priority",
                            0,
                        ),
                    }
                )
            )

        result = {
            "assessment": assessment,
            "plan": plan,
            "queued": queued,
        }

        self._history.append(
            result
        )

        return result

    def process(self):
        item = self.queue.dequeue()

        return item

    def history(self):
        return self._history
