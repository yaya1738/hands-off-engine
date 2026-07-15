from typing import Any, Callable, Dict, List


class FactoryDecisionPolicy:
    def __init__(self):
        self._rules: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def add_rule(
        self,
        decision: str,
        rule: Callable,
    ):
        self._rules[decision] = rule

    def evaluate(
        self,
        decision: str,
        context=None,
    ):
        rule = self._rules.get(
            decision
        )

        if not rule:
            result = {
                "decision": decision,
                "permission": "REVIEW",
                "reason": "no_rule",
            }

        else:
            allowed = rule(context)

            result = {
                "decision": decision,
                "permission": (
                    "ALLOW"
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
