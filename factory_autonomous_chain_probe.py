from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("FACTORY AUTONOMOUS CHAIN")
print("=" * 35)

factory.execute(
    {
        "objective": "autonomous chain verification"
    }
)

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

approved = factory.improvement_approval.approve(
    {
        "improvement": improvement
    }
)

options = factory.decision_option_adapter.build_options(improvement)

selected = factory.decision.select_action(options)

action = selected["selected"]

print("GAPS:", len(gaps))
print("TASKS:", len(improvement["tasks"]))
print("APPROVED:", approved.get("status"))
print("ACTION:", type(action).__name__)

print("DONE")
