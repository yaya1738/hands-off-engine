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

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed"),
    "learning_completed": (
        "learning" in result.get("steps_completed", [])
    )
})
