from datetime import datetime, timezone


class FactoryConsolidationIntelligence:

    def __init__(self, runtime):
        self.runtime = runtime


    def analyze(self):

        inventory = self.runtime.component_inventory()

        components = inventory.get(
            "components",
            []
        )

        classifications = {}

        for component in components:

            if component in [
                "governance",
                "decision",
                "execution",
                "learning",
                "optimization",
                "planning",
            ]:
                category = "core_capability"

            elif "improvement" in component:
                category = "improvement_system"

            elif component in [
                "events",
                "replay",
                "observability",
                "report_generator",
            ]:
                category = "memory_observability"

            else:
                category = "review_required"

            classifications[component] = category


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "total_components":
                len(components),

            "classification":
                classifications,

            "status":
                "analysis_complete"
        }
