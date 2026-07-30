from typing import Any, Dict, List

from ai.factory.capability_evolution_advisor import (
    FactoryCapabilityEvolutionAdvisor,
)


class FactoryCapabilityAssessmentRunner:
    def __init__(self):
        self.advisor = FactoryCapabilityEvolutionAdvisor()
        self._history: List[Dict[str, Any]] = []

    def run_assessment(
        self,
        assessment_name: str,
        current_capabilities: List[str],
        desired_capabilities: List[str],
        objective: str,
    ):
        evaluation = self.advisor.evaluate_capabilities(
            current_capabilities,
            desired_capabilities,
        )

        gaps = self.advisor.identify_missing_capability(
            current_capabilities,
            desired_capabilities,
            objective,
        )

        report = {
            "assessment": assessment_name,
            "objective": objective,
            "evaluation": evaluation,
            "gaps": gaps,
            "status": "COMPLETE",
        }

        self._history.append(report)

        return report

    def history(self):
        return self._history
