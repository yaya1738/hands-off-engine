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

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
