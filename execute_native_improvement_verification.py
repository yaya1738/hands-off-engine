from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "NATIVE_IMPROVEMENT_VERIFICATION_LOOP",
    "reason": (
        "Factory currently requires external verification helpers "
        "to confirm improvement outcomes instead of verifying "
        "changes internally"
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
