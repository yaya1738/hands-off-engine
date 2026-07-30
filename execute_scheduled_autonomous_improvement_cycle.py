from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "SCHEDULED_AUTONOMOUS_IMPROVEMENT_CYCLE",
    "reason": (
        "Factory improvement logic currently requires external "
        "invocation. Factory needs a scheduled internal cycle "
        "that continuously assesses, improves, validates, and learns."
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
