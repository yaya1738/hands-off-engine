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

print({
    "status": "SUBMITTED",
    "result": r.submit_goal(goal)
})
