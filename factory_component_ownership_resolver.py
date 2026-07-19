from datetime import datetime, timezone


class FactoryComponentOwnershipResolver:

    def resolve(self, consolidation_plan):

        review_items = consolidation_plan.get(
            "review",
            []
        )

        ownership = {}

        for component in review_items:

            if component.startswith("improvement_"):
                owner = "improvement_system"

            elif component.startswith("development_"):
                owner = "development_system"

            elif component.startswith("goal_"):
                owner = "goal_system"

            elif component in [
                "feedback_engine",
                "trend_analyzer",
                "change_impact_analyzer",
            ]:
                owner = "intelligence_system"

            elif component in [
                "meta_optimizer",
            ]:
                owner = "optimization_system"

            else:
                owner = "runtime_core"


            ownership[component] = {
                "owner": owner,
                "action": "preserve_under_owner"
            }


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_component_ownership_resolver",

            "ownership":
                ownership,

            "status":
                "ownership_resolved"
        }
