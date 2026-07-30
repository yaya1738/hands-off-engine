from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "IMPROVEMENT_OUTCOME_INTEGRATION_LAYER",
    "reason": (
        "Factory improvement workflows execute successfully, "
        "but completed improvements are not appearing as "
        "applied artifacts or capability history"
    )
}

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
