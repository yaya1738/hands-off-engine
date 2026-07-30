
from typing import Dict, Any, List


class FactoryLearningImprovementAdapter:
    def __init__(self, learning_loop=None):
        self.learning_loop = learning_loop
        self._history: List[Dict[str, Any]] = []

    def generate_gap_assessment(self):
        history = []

        if self.learning_loop:
            history = self.learning_loop.history()

        gaps = []

        for item in history:
            outcome = item.get("outcome", {})

            action = outcome.get("action", {})

            if not isinstance(action, dict):
                action = {
                    "type": action
                }

            if action.get("type") == "autonomous_failure_recovery":
                failure = action.get("failure", {})

                if not isinstance(failure, dict):
                    failure = {
                        "error": str(failure)
                    }

                gaps.append(
                    f"prevent recurring failure: {failure.get('error')}"
                )

        result = {
            "gaps": gaps,
            "health": 0 if gaps else 1,
            "context": "learning derived failure analysis",
            "target": "factory_runtime",
            "development_type": "preventive_self_improvement",
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
