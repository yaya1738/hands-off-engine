from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "WIRE_CHANGE_VALIDATION_INTO_IMPROVEMENT_EXECUTION",
    "reason": (
        "Native validation exists but improvement execution paths "
        "do not invoke validation before audit and learning"
    )
}

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
