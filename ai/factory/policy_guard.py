from typing import Any, Callable, Dict, List


class FactoryPolicyGuard:
    def __init__(self):
        self._rules: Dict[str, Callable] = {}

    def add_rule(
        self,
        action: str,
        rule: Callable,
    ) -> None:
        self._rules[action] = rule

    def check(
        self,
        action: str,
        context: Any = None,
    ) -> Dict[str, Any]:

        rule = self._rules.get(action)

        if not rule:
            return {
                "action": action,
                "allowed": True,
                "reason": "no_rule",
            }

        allowed = rule(context)

        return {
            "action": action,
            "allowed": allowed,
            "reason": (
                "approved"
                if allowed
                else "blocked"
            ),
        }

    def list_rules(self):
        return list(self._rules.keys())
