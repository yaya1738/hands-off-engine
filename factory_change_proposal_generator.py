from datetime import datetime, timezone


class FactoryChangeProposalGenerator:

    def generate(self, governance_report):

        proposals = []

        approvals = governance_report.get(
            "approvals",
            {}
        )

        for component, rule in approvals.items():

            proposals.append(
                {
                    "component": component,
                    "owner": rule["owner"],
                    "requested_action": "analyze_improvement",
                    "permission": rule["allowed_action"],
                    "risk_level": "unknown",
                    "requires_approval": True,
                }
            )

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_change_proposal_generator",

            "proposal_count":
                len(proposals),

            "proposals":
                proposals,

            "status":
                "proposals_generated"
        }
