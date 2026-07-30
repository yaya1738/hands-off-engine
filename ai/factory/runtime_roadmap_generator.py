from typing import Any, Dict, List

from ai.factory.improvement_prioritizer import (
    FactoryImprovementPrioritizer,
)


class FactoryRuntimeRoadmapGenerator:
    def __init__(self):
        self.prioritizer = FactoryImprovementPrioritizer()
        self._history: List[Dict[str, Any]] = []

    def generate(
        self,
        assessment_report: Dict[str, Any],
    ):
        gaps = (
            assessment_report
            .get("gaps", {})
            .get("gap", {})
            .get("missing_capabilities", [])
        )

        roadmap = self.prioritizer.prioritize(
            gaps
        )

        result = {
            "assessment": assessment_report.get(
                "assessment",
                "unknown",
            ),
            "roadmap": roadmap,
            "status": "GENERATED",
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
