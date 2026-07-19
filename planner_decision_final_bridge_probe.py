from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.execute(
    {
        "objective": "planner decision final bridge"
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

options = factory.decision_option_adapter.build_options(plan)

decision = factory.decision.evaluate_options(options)

print("PLANNER → DECISION")
print("=" * 30)
print("TASKS:", len(plan.get("tasks", [])))
print("OPTIONS:", len(options))
print("DECISION TYPE:", type(decision).__name__)

print("DONE")
