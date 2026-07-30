from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_IMPROVEMENT_INVOCATION_MANAGER",
    "reason": (
        "Factory improvement cycle requires autonomous "
        "contract discovery, invocation, recovery, and learning"
    )
}

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "goal": goal,
    "result": result
})
