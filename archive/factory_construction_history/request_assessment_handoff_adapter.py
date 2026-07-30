from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_ASSESSMENT_HANDOFF_ADAPTER",
    "reason": (
        "Autonomous improvement loop must adapt runtime state into "
        "FactorySelfAssessment.assess(metrics) contract automatically."
    )
}

print(r.submit_goal(goal))
