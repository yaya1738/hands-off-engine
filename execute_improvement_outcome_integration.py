from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "IMPROVEMENT_OUTCOME_INTEGRATION_LAYER",
    "reason": (
        "Factory improvement workflows execute successfully, "
        "but completed improvements are not appearing as "
        "applied artifacts or capability history"
    )
}

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed"),
    "learning_completed": (
        "learning" in result.get("steps_completed", [])
    ),
    "audit_available": hasattr(
        r,
        "improvement_audit"
    )
})
