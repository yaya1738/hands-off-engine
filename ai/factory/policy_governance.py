from typing import Any, Dict, List


class FactoryPolicyGovernance:
    def __init__(self):
        self.policies: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def create_policy(
        self,
        name: str,
        policy: Dict[str, Any],
    ):
        self.policies[name] = policy

        result = {
            "created": True,
            "policy": name,
        }

        self._history.append(result)

        return result

    def evaluate_policy(
        self,
        name: str,
        context: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "policy": name,
            "context": context,
        }

        self._history.append(result)

        return result

    def enforce_policy(
        self,
        name: str,
        action: Dict[str, Any],
    ):
        result = {
            "enforced": True,
            "policy": name,
            "action": action,
        }

        self._history.append(result)

        return result

    def update_policy(
        self,
        name: str,
        changes: Dict[str, Any],
    ):
        self.policies.setdefault(
            name,
            {}
        ).update(changes)

        result = {
            "updated": True,
            "policy": name,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
