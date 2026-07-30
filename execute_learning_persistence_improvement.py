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

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed"),
    "learning_available": hasattr(r, "learning"),
    "audit_available": hasattr(r, "improvement_audit")
})
