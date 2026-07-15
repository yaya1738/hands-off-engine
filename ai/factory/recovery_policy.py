from typing import Any, Callable, Dict, List


class FactoryRecoveryPolicy:
    def __init__(self):
        self._rules: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def add_rule(
        self,
        component: str,
        rule: Callable,
    ):
        self._rules[component] = rule

    def evaluate(
        self,
        component: str,
        context=None,
    ):
        rule = self._rules.get(
            component
        )

        if not rule:
            result = {
                "component": component,
                "permission": "CAUTION",
                "reason": "no_rule",
            }

        else:
            allowed = rule(context)

            result = {
                "component": component,
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
