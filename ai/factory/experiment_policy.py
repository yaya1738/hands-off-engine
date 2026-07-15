from typing import Any, Callable, Dict, List


class FactoryExperimentPolicy:
    def __init__(self):
        self._rules: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def add_rule(
        self,
        experiment: str,
        rule: Callable,
    ):
        self._rules[experiment] = rule

    def evaluate(
        self,
        experiment: str,
        context=None,
    ):
        rule = self._rules.get(
            experiment
        )

        if not rule:
            result = {
                "experiment": experiment,
                "permission": "REVIEW",
                "reason": "no_rule",
            }

        else:
            allowed = rule(context)

            result = {
                "experiment": experiment,
                "permission": (
                    "SAFE"
                    if allowed
                    else "BLOCK"
                ),
                "reason": (
                    "approved"
                    if allowed
                    else "denied"
                ),
            }

        self._history.append(result)

        return result

    def history(self):
        return self._history
