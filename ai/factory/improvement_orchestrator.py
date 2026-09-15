from typing import Any, Dict, List

from ai.factory.assessment_bus_publisher import FactoryAssessmentBusPublisher


class FactoryImprovementOrchestrator:
    def __init__(
        self,
        assessor=None,
        planner=None,
        queue=None,
        assessment_publisher=None,
    ):
        self.assessor = assessor
        self.planner = planner
        self.queue = queue
        self.assessment_publisher = assessment_publisher or FactoryAssessmentBusPublisher()
        self._history: List[Dict[str, Any]] = []

    def run_cycle(
        self,
        metrics: Dict[str, Any],
    ):
        assessment = self.assessor.assess(
            metrics
        )

        if self.assessment_publisher is not None:
            self.assessment_publisher.publish(assessment)

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
                        "capability_context": plan.get(
                            "capability_context",
                            {},
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
