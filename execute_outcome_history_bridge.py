from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "OUTCOME_TO_FACTORY_HISTORY_BRIDGE",
    "reason": (
        "Improvement outcomes execute and audit exists, "
        "but completed improvement results are not entering "
        "Factory runtime history"
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
