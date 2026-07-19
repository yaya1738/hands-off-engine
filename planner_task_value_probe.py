from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.execute(
    {
        "objective": "task shape check"
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

print("TASK VALUE SHAPE")
print("=" * 35)

tasks = plan.get("tasks")

print("TYPE:", type(tasks).__name__)
print("COUNT:", len(tasks))

if tasks:
    print("FIRST TYPE:", type(tasks[0]).__name__)
    if isinstance(tasks[0], dict):
        print("FIRST KEYS:", list(tasks[0].keys()))

print("DONE")
