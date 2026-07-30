from datetime import datetime, timezone


class FactoryCapabilityGapAnalyzer:

    REQUIRED_CAPABILITIES = [
        "objective_management",
        "decision_generation",
        "planning",
        "execution",
        "self_improvement",
        "adaptation",
        "feedback_processing",
        "memory",
        "reporting",
        "capability_management",
    ]

    def __init__(self, runtime):
        self.runtime = runtime


    def analyze(self):

        graph = self.runtime.capability_graph_intelligence.analyze()

        existing = set()

        for item in graph.get(
            "capability_graph",
            {}
        ).values():
            existing.add(
                item.get(
                    "provides"
                )
            )

        missing = [
            capability
            for capability in self.REQUIRED_CAPABILITIES
            if capability not in existing
        ]

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "existing_capabilities":
                sorted(existing),

            "missing_capabilities":
                missing,

            "status":
                "gap_analysis_complete",
        }
