from typing import Any, Dict, List


class FactoryDecisionIntelligence:
    def __init__(self):
        self.decisions: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_decision(
        self,
        decision: Dict[str, Any],
    ):
        self.decisions.append(decision)

        result = {
            "created": True,
            "decision": decision,
        }

        self._history.append(result)

        return result

    def evaluate_options(
        self,
        options: List[Dict[str, Any]],
    ):
        result = {
            "evaluated": True,
            "count": len(options),
        }

        self._history.append(result)

        return result

    def score_decision(
        self,
        decision: Dict[str, Any],
    ):
        result = {
            "scored": True,
            "decision": decision,
        }

        self._history.append(result)

        return result

    def select_action(
        self,
        actions: List[Dict[str, Any]],
    ):
        result = {
            "selected": True,
            "count": len(actions),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
