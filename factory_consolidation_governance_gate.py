from datetime import datetime, timezone


class FactoryConsolidationGovernanceGate:

    def evaluate(self, ownership_report):

        ownership = ownership_report.get(
            "ownership",
            {}
        )

        approvals = {}

        for component, info in ownership.items():

            owner = info.get(
                "owner"
            )

            if owner in [
                "runtime_core",
                "optimization_system",
                "improvement_system",
            ]:
                action = "simulation_only"

            else:
                action = "review_before_change"


            approvals[component] = {
                "owner": owner,
                "allowed_action": action,
                "approved": False,
            }


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_consolidation_governance_gate",

            "approvals":
                approvals,

            "status":
                "governance_evaluated"
        }
