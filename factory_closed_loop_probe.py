from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("FACTORY CLOSED LOOP")
print("=" * 35)

factory.execute(
    {
        "objective": "closed loop verification"
    }
)

metrics = factory.observability.metrics

gaps = factory.improvement_assessment.detect_gaps(metrics)

plan = factory.improvement_planner.plan(
    {
        "gaps": gaps
    }
)

options = factory.decision_option_adapter.build_options(plan)

decision = factory.decision.evaluate_options(options)

print("METRICS:", len(metrics))
print("GAPS:", len(gaps))
print("TASKS:", len(plan.get("tasks", [])))
print("OPTIONS:", len(options))
print("DECISION:", type(decision).__name__)

print("DONE")
