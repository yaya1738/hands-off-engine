from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.execute(
    {
        "objective": "planner decision bridge verification"
    }
)

metrics = factory.get_assessment_metrics()
gaps = factory.improvement_assessment.detect_gaps(metrics)

plan = factory.improvement_planner.plan(
    {
        "goal": "improve runtime",
        "tasks": gaps,
        "priority": 1,
        "context": "assessment",
        "target": "factory",
        "development_type": "improvement",
        "components": [],
        "integration_points": [],
        "validation": [],
        "rollback": [],
    }
)

options = factory.decision_option_adapter.build_options(plan)

print("PLANNER → DECISION ADAPTER")
print("=" * 35)
print("OPTIONS TYPE:", type(options).__name__)
print("OPTIONS COUNT:", len(options))

if options:
    print("OPTION KEYS:", list(options[0].keys()))

print("DONE")
