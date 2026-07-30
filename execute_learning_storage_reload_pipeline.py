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

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed"),
    "learning_step_completed": (
        "learning" in result.get("steps_completed", [])
    ),
    "audit_available": hasattr(
        r,
        "improvement_audit"
    )
})
