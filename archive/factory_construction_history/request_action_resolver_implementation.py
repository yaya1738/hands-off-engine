from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "IMPROVEMENT_ACTION_RESOLVER_IMPLEMENTATION",
    "reason": (
        "Factory autonomously creates and approves improvement tasks, "
        "but approved tasks cannot yet be translated into executable "
        "actions for the improvement executor."
    )
}

print({
    "status": "SUBMITTED",
    "result": r.submit_goal(goal)
})
