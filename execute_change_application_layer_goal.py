from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "IMPROVEMENT_CHANGE_APPLICATION_LAYER",
    "reason": (
        "Factory identifies and executes improvement goals, "
        "but verified capability changes are not being applied"
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
