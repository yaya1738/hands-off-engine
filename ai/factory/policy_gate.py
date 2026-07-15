from typing import Dict, Any


class FactoryPolicyGate:
    def __init__(self):
        self.allowed_actions = {
            "continue",
            "review_failures",
            "investigate",
        }

    def evaluate(
        self,
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        action = decision.get(
            "action"
        )

        approved = action in self.allowed_actions

        return {
            "action": action,
            "approved": approved,
            "reason": (
                "policy_allowed"
                if approved
                else "policy_blocked"
            ),
        }
