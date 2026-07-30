from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "CHANGE_VALIDATION_FEEDBACK_BRIDGE",
    "reason": (
        "Factory has native change validation capability, "
        "but validation results are not connected to "
        "improvement audit, capability registry, and learning"
    )
}

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed"),
    "learning_completed": (
        "learning" in result.get("steps_completed", [])
    )
})
