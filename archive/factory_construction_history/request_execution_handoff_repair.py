from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_IMPROVEMENT_EXECUTION_HANDOFF_FAILURE",
    "reason": (
        "Factory autonomous improvement cycle can generate queued "
        "improvements, but the execution handoff requires repair so "
        "existing executor contracts are used automatically."
    )
}

print({
    "status": "SUBMITTED",
    "result": r.submit_goal(goal)
})
