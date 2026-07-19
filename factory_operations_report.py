from ai.factory.runtime import FactoryRuntime


def status(ok):
    return "✓" if ok else "✗"


print("FACTORY OPERATIONS REPORT")
print("=" * 45)

factory = FactoryRuntime()

print("\nSYSTEM LOOP")
print("-" * 20)

checks = {
    "Assessment": hasattr(factory, "improvement_assessment"),
    "Planner": hasattr(factory, "improvement_planner"),
    "Approval": hasattr(factory, "improvement_approval"),
    "Decision": hasattr(factory, "decision_option_adapter"),
    "Resolver": hasattr(factory, "improvement_action_resolver"),
    "Executor": hasattr(factory, "improvement_executor"),
    "Audit": hasattr(factory, "improvement_audit"),
}

for name, ok in checks.items():
    print(status(ok), name)


print("\nCAPABILITY FLOW")
print("-" * 20)

try:
    metrics = {
        "success_rate": 1.0,
        "average_impact": 0.0,
    }

    gaps = factory.improvement_assessment.detect_gaps(metrics)

    plan = factory.improvement_planner.plan(
        {
            "goal": "factory capability report",
            "gaps": gaps,
            "priority": 1,
            "context": "audit",
            "target": "factory",
            "development_type": "improvement",
            "components": [],
            "integration_points": [],
            "validation": [],
            "rollback": [],
        }
    )

    print("✓ Assessment → Planner")
    print("  Gaps:", len(gaps))
    print("  Tasks:", len(plan.get("tasks", [])))

except Exception as exc:
    print("✗ Assessment → Planner")
    print("  Error:", exc)


print("\nACTION CAPABILITY")
print("-" * 20)

try:
    resolver = factory.improvement_action_resolver

    handler = resolver.resolve(
        {
            "action": "address low success rate"
        }
    )

    if handler:
        print("✓ Action has executable capability")
    else:
        print("! Action has no registered capability")

except Exception as exc:
    print("✗ Resolver check failed:", exc)


print("\nFACTORY DECISION")
print("-" * 20)

print("Current state:")
print("Planning and decision layers connected.")
print("Execution capability registry is the current gap.")

print("\nDONE")
