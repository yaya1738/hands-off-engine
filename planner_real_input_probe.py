from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.execute(
    {
        "objective": "planner contract verification"
    }
)

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

print("REAL PLANNER INPUT")
print("=" * 30)
print("GAPS:", len(gaps))
print("TASKS:", len(plan.get("tasks", [])))
print("DONE")
