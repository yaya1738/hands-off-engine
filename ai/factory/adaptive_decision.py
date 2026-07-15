from typing import Any, Dict, List


class FactoryAdaptiveDecision:
    def __init__(
        self,
        feedback=None,
    ):
        self.feedback = feedback
        self._history: List[Dict[str, Any]] = []
        self.bias = 0

    def learn(
        self,
        recommendation: Dict[str, Any],
    ):
        if recommendation.get(
            "recommendation"
        ) == "OPTIMIZE_IMPROVEMENT_FLOW":
            self.bias += 1

        result = {
            "bias": self.bias,
        }

        self._history.append(
            result
        )

        return result

    def decide(
        self,
        state: Dict[str, Any],
    ):
        if state.get(
            "health"
        ) == "DOWN":
            decision = "RECOVER"

        elif (
            state.get(
                "success_rate",
                1,
            ) < 0.8
            or self.bias > 0
        ):
            decision = "IMPROVE"

        else:
            decision = "CONTINUE"

        result = {
            "decision": decision,
        }

        self._history.append(
            result
        )

        return result

    def adjust(self):
        return {
            "bias": self.bias,
        }

    def history(self):
        return self._history
