from typing import Any, Dict, List


class FactoryFeedbackEngine:
    def __init__(
        self,
        memory=None,
    ):
        self.memory = memory
        self._history: List[Dict[str, Any]] = []

    def analyze(self):
        items = getattr(
            self.memory,
            "_memory",
            [],
        )

        patterns = {}

        for item in items:
            action = item.get(
                "action"
            )
            if action:
                patterns[action] = patterns.get(
                    action,
                    0,
                ) + 1

        result = {
            "patterns": patterns,
        }

        self._history.append(
            result
        )

        return result


    def recommend(self):
        analysis = self.analyze()

        if analysis.get(
            "patterns",
            {},
        ).get(
            "IMPROVE",
            0,
        ):
            recommendation = "OPTIMIZE_IMPROVEMENT_FLOW"
        else:
            recommendation = "CONTINUE_MONITORING"

        return {
            "recommendation": recommendation,
        }


    def history(self):
        return self._history


    def score(
        self,
        result,
    ):
        score = 1 if result.get(
            "success"
        ) else 0

        output = {
            "score": score,
        }

        self._history.append(
            output
        )

        return output


    def history(self):
        return self._history
