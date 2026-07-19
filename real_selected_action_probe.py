from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

metrics = factory.get_assessment_metrics()
gaps = factory.improvement_assessment.detect_gaps(metrics)

improvement = factory.improvement_planner.plan(
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

options = factory.decision_option_adapter.build_options(improvement)
selected = factory.decision.select_action(options)

print("REAL ACTION")
print("=" * 30)

print(selected["selected"])

print("DONE")
