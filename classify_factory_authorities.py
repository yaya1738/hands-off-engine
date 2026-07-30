from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

groups = {
    "EXECUTION_AUTHORITY": [
        "execution",
        "execution_handoff",
        "improvement_executor",
        "checkpoint_executor",
        "action_router",
    ],
    "DECISION_AUTHORITY": [
        "decision",
        "strategy_manager",
        "adaptive_decision",
        "decision_option_adapter",
        "capability_evolution_decision",
    ],
    "LEARNING_AUTHORITY": [
        "learning",
        "learning_loop",
        "learning_improvement_adapter",
        "feedback_engine",
        "recommendations",
    ],
    "IMPROVEMENT_AUTHORITY": [
        "improvement_orchestrator",
        "improvement_queue",
        "improvement_planner",
        "improvement_approval",
        "improvement_audit",
    ],
    "GOVERNANCE_AUTHORITY": [
        "governance",
        "integration_supervisor",
        "gap_repair_controller",
        "integrity_checker",
    ],
}

for authority, items in groups.items():
    print("\n====", authority, "====")
    for item in items:
        obj = getattr(r, item, None)
        print(
            item,
            "->",
            type(obj).__name__ if obj else "MISSING"
        )

