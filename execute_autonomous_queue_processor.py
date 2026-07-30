from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_IMPROVEMENT_QUEUE_PROCESSOR",
    "reason": (
        "Factory can assess itself, detect gaps, plan improvements, "
        "and create queued actions, but queued improvements require "
        "automatic processing through execution, validation, audit, "
        "and learning."
    )
}

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed")
})
