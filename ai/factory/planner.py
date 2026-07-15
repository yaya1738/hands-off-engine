from typing import Dict, List


class FactoryPlanner:
    def plan(self, goal: Dict[str, str]) -> List[str]:
        objective = goal.get("goal", "")

        if not objective:
            return []

        return [
            f"analyze:{objective}",
            f"implement:{objective}",
            f"test:{objective}",
            f"review:{objective}",
        ]
