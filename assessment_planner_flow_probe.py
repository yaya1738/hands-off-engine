from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.execute(
    {
        "objective": "planner bridge verification"
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

print("ASSESSMENT → PLANNER FLOW")
print("=" * 35)
print("GAPS:", len(gaps))
print("PLAN TYPE:", type(plan).__name__)

if isinstance(plan, dict):
    print("PLAN KEYS:", list(plan.keys()))

print("DONE")
