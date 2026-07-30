from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "SELF_ASSESSMENT_INTERFACE_ADAPTER",
    "reason": (
        "Autonomous improvement validation reached FactorySelfAssessment "
        "but the validation interface requires metrics input."
    )
}

print(r.execute(goal))
