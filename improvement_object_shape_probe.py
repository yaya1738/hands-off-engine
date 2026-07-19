from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

metrics = factory.get_assessment_metrics()
gaps = factory.improvement_assessment.detect_gaps(metrics)

plan = factory.improvement_planner.plan(
    {
        "goal": "improve factory performance",
        "gaps": gaps,
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

print("IMPROVEMENT OBJECT SEARCH")
print("=" * 35)

print("PLAN KEYS:", list(plan.keys()))

for key, value in plan.items():
    if "improvement" in key.lower() or "id" in key.lower():
        print(key, "=>", type(value).__name__)

print("DONE")
