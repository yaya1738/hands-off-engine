from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "OUTCOME_TO_FACTORY_HISTORY_BRIDGE",
    "reason": (
        "Improvement outcomes execute and audit exists, "
        "but completed improvement results are not entering "
        "Factory runtime history"
    )
}

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
