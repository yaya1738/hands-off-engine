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

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
