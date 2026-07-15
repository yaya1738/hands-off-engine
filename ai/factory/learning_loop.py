from typing import Any, Dict, List


class FactoryLearningLoop:
    def __init__(self):
        self.outcomes: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def record_outcome(
        self,
        outcome: Dict[str, Any],
    ):
        self.outcomes.append(
            outcome
        )

        result = {
            "recorded": True,
            "outcome": outcome,
        }

        self._history.append(result)

        return result

    def analyze_feedback(
        self,
        feedback: Dict[str, Any],
    ):
        result = {
            "analyzed": True,
            "feedback": feedback,
        }

        self._history.append(result)

        return result

    def update_model(
        self,
        update: Dict[str, Any],
    ):
        result = {
            "updated": True,
            "model_update": update,
        }

        self._history.append(result)

        return result

    def generate_improvement(
        self,
        idea: Dict[str, Any],
    ):
        self.improvements.append(
            idea
        )

        result = {
            "generated": True,
            "improvement": idea,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
