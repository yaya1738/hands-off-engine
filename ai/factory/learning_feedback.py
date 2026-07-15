from typing import Any, Dict, List


class FactoryLearningFeedback:
    def __init__(
        self,
        memory=None,
    ):
        self.memory = memory
        self.decisions: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def record_decision(
        self,
        decision: Dict[str, Any],
    ):
        self.decisions.append(
            decision
        )

        if self.memory:
            self.memory.remember(
                {
                    "type": "DECISION",
                    "data": decision,
                }
            )

        result = {
            "recorded": True,
        }

        self._history.append(
            result
        )

        return result

    def record_result(
        self,
        outcome: Dict[str, Any],
    ):
        self.results.append(
            outcome
        )

        if self.memory:
            self.memory.record_outcome(
                outcome
            )

        result = {
            "recorded": True,
        }

        self._history.append(
            result
        )

        return result

    def evaluate(self):
        result = {
            "decisions": len(
                self.decisions
            ),
            "results": len(
                self.results
            ),
        }

        self._history.append(
            result
        )

        return result

    def learn(self):
        evaluation = self.evaluate()

        result = {
            "learned": True,
            "evaluation": evaluation,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
