from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "SELF_ASSESSMENT_INTERFACE_ADAPTER",
    "reason": (
        "Autonomous improvement validation reached FactorySelfAssessment "
        "but the validation interface requires metrics input. "
        "Factory needs an internal adapter so autonomous validation can "
        "call assessment correctly."
    )
}

print({
    "status": "SUBMITTED",
    "result": r.submit_goal(goal)
})
