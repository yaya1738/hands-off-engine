from typing import Any, Dict, List


class FactoryDevelopmentAdvisor:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def analyze(
        self,
        findings: Dict[str, Any],
    ):
        recommendations = []

        for gap in findings.get("gaps", []):
            recommendations.append(
                {
                    "type": "development_improvement",
                    "target": gap,
                    "risk": "low",
                    "requires_approval": True,
                }
            )

        result = {
            "recommendations": recommendations,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
