from datetime import datetime, timezone


class FactoryRoleAnalysisIntelligence:

    def __init__(self, runtime):
        self.runtime = runtime


    def analyze(self):

        graph = (
            self.runtime.autonomy
            .capability_graph_analysis()
        )

        capabilities = graph["capability_graph"]

        roles = {}

        for name, data in capabilities.items():

            capability = data["provides"]

            roles[name] = {
                "capability": capability,
                "role": self.classify_role(
                    name,
                    capability
                )
            }

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "roles":
                roles,

            "status":
                "role_analysis_complete"
        }


    def classify_role(self, name, capability):

        if "management" in name:
            return "controller"

        if "optimizer" in name:
            return "optimizer"

        if "engine" in name:
            return "processor"

        if "loop" in name:
            return "feedback_cycle"

        if "pipeline" in name:
            return "workflow"

        if "executor" in name or name == "execution":
            return "executor"

        if "audit" in name or "checker" in name:
            return "validator"

        return "support_component"
