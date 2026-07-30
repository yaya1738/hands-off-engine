from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_IMPROVEMENT_EXECUTOR_ADAPTER",
    "reason": (
        "Autonomous improvement flow reaches the existing executor, "
        "but queued improvement actions require an adapter to match "
        "the executor's existing contract automatically."
    )
}

print({
    "status": "SUBMITTED",
    "result": r.submit_goal(goal)
})
