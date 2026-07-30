from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_REPAIR_MANAGER",
    "reason": "Factory requires autonomous detection, repair, verification, and learning loop"
}

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "goal": goal,
    "result": result
})
