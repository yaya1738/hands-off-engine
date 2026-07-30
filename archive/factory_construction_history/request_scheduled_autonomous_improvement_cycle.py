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

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
