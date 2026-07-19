from datetime import datetime, timezone


class FactoryChangeImpactAnalyzer:

    def analyze(self, proposal_report):

        impacts = []

        for proposal in proposal_report.get(
            "proposals",
            []
        ):

            permission = proposal.get(
                "permission"
            )

            if permission == "simulation_only":
                risk = "low"
                confidence = 0.9

            else:
                risk = "medium"
                confidence = 0.7


            impacts.append(
                {
                    "component":
                        proposal["component"],

                    "owner":
                        proposal["owner"],

                    "risk_level":
                        risk,

                    "expected_benefit":
                        "potential_capability_improvement",

                    "affected_scope":
                        proposal["owner"],

                    "rollback_required":
                        True,

                    "confidence":
                        confidence,

                    "approval_required":
                        proposal["requires_approval"]
                }
            )


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_change_impact_analyzer",

            "impact_count":
                len(impacts),

            "impacts":
                impacts,

            "status":
                "impact_analysis_complete"
        }
