from ai.factory.runtime import FactoryRuntime

runtime = FactoryRuntime()

checks = {
    "approval": runtime.improvement_approval,
    "executor": runtime.improvement_executor,
    "audit": runtime.improvement_audit,
    "pipeline": runtime.development_pipeline,
    "feedback": runtime.feedback_engine,
    "learning": runtime.learning_loop,
    "decision": runtime.decision,
    "simulation": runtime.simulation,
}

print("FACTORY TRANSITION AUDIT")
print("=" * 35)

for name, obj in checks.items():
    print()
    print(name.upper())
    print("TYPE:", type(obj).__name__)

    methods = [
        m for m in dir(obj)
        if not m.startswith("_")
    ]

    important = [
        m for m in methods
        if any(
            word in m.lower()
            for word in [
                "approve",
                "execute",
                "validate",
                "complete",
                "record",
                "learn",
                "feedback",
                "history",
                "run",
            ]
        )
    ]

    print("METHODS:", important)

print()
print("RUNTIME METHODS")
print(
    [
        m for m in dir(runtime)
        if any(
            word in m.lower()
            for word in [
                "execute",
                "approve",
                "complete",
                "validate",
                "learn",
                "improve",
            ]
        )
    ]
)
