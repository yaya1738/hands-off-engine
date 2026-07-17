from datetime import datetime, timezone


class FactoryChangeApprovalAuthority:

    def evaluate(self, impact_report):

        decisions = []

        for impact in impact_report.get(
            "impacts",
            []
        ):

            risk = impact.get(
                "risk_level"
            )

            confidence = impact.get(
                "confidence",
                0
            )

            if (
                risk == "low"
                and confidence >= 0.9
            ):
                decision = "approve_simulation"

            elif (
                risk == "medium"
            ):
                decision = "request_review"

            else:
                decision = "reject"


            decisions.append(
                {
                    "component":
                        impact["component"],

                    "owner":
                        impact["owner"],

                    "decision":
                        decision,

                    "reason":
                        "risk_and_confidence_evaluation",

                    "execution_allowed":
                        False
                }
            )


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_change_approval_authority",

            "decisions":
                decisions,

            "status":
                "approval_evaluation_complete"
        }
