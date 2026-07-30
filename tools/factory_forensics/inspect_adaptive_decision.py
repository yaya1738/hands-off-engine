from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "TEST_SELF_IMPROVEMENT_ROUTING"
}

metrics = r.get_assessment_metrics()

decision = r.adaptive_decision.decide(
    {
        "health": "LOW",
        "success_rate": 0,
        "goal": goal,
    }
)

print(decision)
