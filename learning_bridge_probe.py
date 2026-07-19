from ai.factory.runtime import FactoryRuntime

runtime = FactoryRuntime()

print("BEFORE LEARNING:", len(runtime.learning_loop.history()))

result = runtime.execute_approved_improvement(
    {
        "status": "APPROVED",
        "name": "bridge_test",
    },
    lambda: {"success": True}
)

print("RESULT:", result["status"])
print("AFTER LEARNING:", len(runtime.learning_loop.history()))
print("FEEDBACK HISTORY:", len(runtime.feedback_engine.history()))
print("AUDIT:", len(runtime.improvement_audit.history()))
