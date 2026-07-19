from ai.factory.runtime import FactoryRuntime

runtime = FactoryRuntime()

blocked = runtime.process_approved_improvement(
    {
        "status": "PENDING",
        "name": "test_unapproved"
    },
    lambda: "SHOULD_NOT_RUN"
)

print("RESULT:", blocked)
print("AUDIT:", len(runtime.improvement_audit.history()))
