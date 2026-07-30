from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "PERSISTENT_LEARNING_STATE",
    "reason": (
        "Factory learning executes but experiences "
        "are not persisted across runtime initialization"
    )
}

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
