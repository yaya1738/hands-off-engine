from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "LEARNING_STATE_STORAGE_AND_RELOAD_PIPELINE",
    "reason": (
        "Learning execution succeeds but new runtime instances "
        "do not reload prior experiences"
    )
}

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
