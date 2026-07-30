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

print({
    "status": "SUBMITTED",
    "result": r.submit_goal(goal)
})
