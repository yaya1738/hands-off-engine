from typing import Any, Dict, List


class FactoryPlanningIntelligence:
    def __init__(self):
        self.plans: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_plan(
        self,
        plan: Dict[str, Any],
    ):
        self.plans.append(plan)

        result = {
            "created": True,
            "plan": plan,
        }

        self._history.append(result)

        return result

    def analyze_constraints(
        self,
        constraints: Dict[str, Any],
    ):
        result = {
            "analyzed": True,
            "constraints": constraints,
        }

        self._history.append(result)

        return result

    def allocate_resources(
        self,
        resources: Dict[str, Any],
    ):
        result = {
            "allocated": True,
            "resources": resources,
        }

        self._history.append(result)

        return result

    def evaluate_plan(
        self,
        plan: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "plan": plan,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
