from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_IMPROVEMENT_LOOP_CLOSURE_ASSESSMENT",
    "reason": (
        "Factory must autonomously evaluate whether its existing "
        "assessment, gap detection, goal generation, planning, "
        "execution, validation, audit, and learning components "
        "form a closed self-improvement loop"
    )
}

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
