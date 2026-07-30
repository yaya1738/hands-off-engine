from typing import Any, Dict, List


class FactoryImprovementPrioritizer:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def prioritize(
        self,
        gaps: List[str],
    ):
        priority_rules = {
            "lifecycle_coordination": 100,
            "unified_bootstrap": 90,
            "capability_registry": 80,
            "event_driven_orchestration": 70,
            "state_management": 60,
            "runtime_health_monitoring": 50,
        }

        ranked = sorted(
            gaps,
            key=lambda item: priority_rules.get(item, 10),
            reverse=True,
        )

        result = {
            "ranked_improvements": ranked,
            "count": len(ranked),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
