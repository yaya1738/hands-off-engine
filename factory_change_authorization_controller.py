from datetime import datetime, timezone


class FactoryChangeAuthorizationController:

    def __init__(self):
        self.component = "factory_change_authorization_controller"

    def authorize(self, validation_result):

        decisions = []

        for item in validation_result.get("validations", []):

            if item.get("validation") == "passed":
                decision = "approved_for_execution_review"
            else:
                decision = "blocked_pending_review"

            decisions.append(
                {
                    "component": item.get("component"),
                    "owner": item.get("owner"),
                    "authorization": decision,
                    "execution_allowed": False,
                    "reason": "controlled_authorization_boundary",
                }
            )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": self.component,
            "authorization_count": len(decisions),
            "decisions": decisions,
            "status": "authorization_complete",
        }
