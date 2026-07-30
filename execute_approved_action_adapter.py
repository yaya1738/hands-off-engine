from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_APPROVED_ACTION_ADAPTER",
    "reason": (
        "Autonomous improvement reaches approval successfully, "
        "but approved improvement outputs require normalization "
        "before executor invocation."
    )
}

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed")
})
