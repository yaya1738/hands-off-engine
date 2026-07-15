from typing import Any, Dict, List


class FactoryPolicyEnforcement:
    def __init__(self):
        self.policies: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def register_policy(
        self,
        policy: Dict[str, Any],
    ):
        self.policies.append(
            policy
        )

        result = {
            "registered": True,
            "policy": policy,
        }

        self._history.append(
            result
        )

        return result

    def evaluate_policy(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "allowed": True,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def enforce_policy(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "enforced": True,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def exceptions(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "exception": False,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
