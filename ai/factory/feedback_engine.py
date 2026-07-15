from typing import Any, Dict, List


class FactoryFeedbackEngine:
    def __init__(
        self,
        memory=None,
    ):
        self.memory = memory
        self._history: List[Dict[str, Any]] = []

    def analyze(self):
        if not self.memory:
            result = {
                "patterns": {},
            }

        else:
            result = {
                "patterns": self.memory.patterns(),
            }

        self._history.append(
            result
        )

        return result

    def score(
        self,
        experience: Dict[str, Any],
    ):
        success = experience.get(
            "success",
            False,
        )

        score = 1 if success else 0

        result = {
            "score": score,
        }

        self._history.append(
            result
        )

        return result

    def recommend(self):
        analysis = self.analyze()

        patterns = analysis.get(
            "patterns",
            {},
        )

        if patterns.get(
            "IMPROVE",
            0,
        ):
            result = {
                "recommendation": "OPTIMIZE_IMPROVEMENT_FLOW",
            }

        else:
            result = {
                "recommendation": "CONTINUE_MONITORING",
            }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
