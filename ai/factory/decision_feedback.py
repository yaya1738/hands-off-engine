from typing import Any, Dict, List


class FactoryDecisionFeedback:
    def __init__(self):
        self._decisions: List[Dict[str, Any]] = []

    def record_decision(
        self,
        decision: Dict[str, Any],
    ):
        entry = {
            "decision": decision,
            "outcome": None,
        }

        self._decisions.append(
            entry
        )

        return entry

    def record_outcome(
        self,
        entry: Dict[str, Any],
        outcome: Dict[str, Any],
    ):
        entry["outcome"] = outcome

        return entry

    def evaluate(
        self,
        entry: Dict[str, Any],
    ):
        outcome = entry.get(
            "outcome"
        )

        if not outcome:
            return {
                "status": "UNKNOWN",
            }

        success = outcome.get(
            "success",
            False,
        )

        return {
            "status": (
                "IMPROVED"
                if success
                else "FAILED"
            ),
            "impact": outcome.get(
                "impact",
                0,
            ),
        }

    def history(self):
        return self._decisions
