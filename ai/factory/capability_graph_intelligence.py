from datetime import datetime, timezone


class FactoryCapabilityGraphIntelligence:

    def __init__(self, runtime):
        self.runtime = runtime


    def analyze(self):

        inventory = self.runtime.component_inventory()

        components = inventory.get(
            "components",
            []
        )

        graph = {}

        for component in components:

            graph[component] = {
                "provides": self.infer_capability(component),
                "status": "active",
                "redundancy": 0,
            }

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component_count":
                len(components),

            "capability_graph":
                graph,

            "status":
                "graph_complete"
        }


    def infer_capability(self, name):

        mappings = {
            "goal": "objective_management",
            "decision": "decision_generation",
            "planning": "planning",
            "execution": "execution",
            "learning": "adaptation",
            "optimization": "optimization",
            "feedback": "feedback_processing",
            "improvement": "self_improvement",
            "state": "memory",
            "event": "event_memory",
            "report": "reporting",
        }

        for key, value in mappings.items():

            if key in name:
                return value

        return "general_factory_capability"
