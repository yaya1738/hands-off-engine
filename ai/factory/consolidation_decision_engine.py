from datetime import datetime, timezone


class FactoryConsolidationDecisionEngine:

    def __init__(self, runtime):
        self.runtime = runtime


    def analyze(self):

        usage = (
            self.runtime.autonomy
            .usage_analysis()["usage"]
        )

        graph = (
            self.runtime.autonomy
            .capability_graph_analysis()["capability_graph"]
        )

        decisions = {}

        for name, data in graph.items():

            refs = usage[name]["references_found"]

            capability = data["provides"]

            if refs >= 10:
                decision = "preserve"

            elif refs <= 1:
                decision = "review_owner"

            else:
                decision = "preserve"

            decisions[name] = {
                "capability": capability,
                "references": refs,
                "decision": decision
            }


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "decisions":
                decisions,

            "status":
                "consolidation_analysis_complete"
        }
