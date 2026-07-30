from datetime import datetime, timezone


class FactoryAuthorityRegistry:

    def __init__(self, runtime=None):
        self.runtime = runtime

    def registry(self):

        return {

            # Core authorities

            "execution": [
                "execution",
                "execution_handoff",
                "improvement_executor",
                "checkpoint_executor",
                "action_router",
            ],

            "decision": [
                "decision",
                "strategy_manager",
                "adaptive_decision",
                "capability_evolution_decision",
                "decision_option_adapter",
            ],

            "learning": [
                "learning",
                "learning_loop",
                "learning_improvement_adapter",
                "feedback_engine",
                "recommendations",
            ],

            "improvement": [
                "improvement_orchestrator",
                "improvement_queue",
                "improvement_planner",
                "improvement_approval",
                "improvement_audit",
            ],

            "governance": [
                "governance",
                "integration_supervisor",
                "gap_repair_controller",
                "integrity_checker",
            ],


            # Support authorities

            "artifact": [
                "artifact_registry",
                "registry",
            ],

            "capability": [
                "capability_onboarding",
                "improvement_capability_registry",
                "capability_graph_intelligence",
                "capability_gap_analyzer",
                "capability_consolidation_loader",
                "capability_evolution_context",
            ],

            "development": [
                "development_advisor",
                "development_pipeline",
                "development_translator",
                "development_tracker",
                "lifecycle_trace",
            ],

            "goals": [
                "goal_management",
                "goal_optimizer",
                "goal_genesis",
            ],

            "resources": [
                "resource_allocator",
            ],

            "state": [
                "state",
                "events",
                "replay",
                "observability",
            ],

            "intelligence": [
                "diagnostics",
                "meta_optimizer",
                "operations_intelligence",
                "trend_analyzer",
                "change_impact_analyzer",
                "change_validation",
                "planning",
                "simulation",
                "optimization",
            ],
        }



    def resolve(self, authority):

        if not self.runtime:
            return None

        components = self.registry().get(
            authority,
            []
        )

        return {
            name:
            getattr(
                self.runtime,
                name,
                None
            )
            for name in components
        }


    def health(self):

        result = {}

        for authority, components in self.registry().items():

            result[authority] = {
                "count": len(components),
                "available": [
                    c for c in components
                    if self.runtime and hasattr(self.runtime,c)
                ]
            }

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "authorities": result
        }
