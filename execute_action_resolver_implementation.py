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

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed")
})
