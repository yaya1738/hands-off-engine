from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

improvement = {
    "name": "executor bridge test",
    "status": "APPROVED",
}

def test_action():
    return {
        "changed": True,
        "message": "test execution"
    }

result = factory.execute_approved_improvement(
    improvement,
    test_action,
)

print("EXECUTION STATUS:")
print(result["status"])

print()

print("EXECUTOR HISTORY COUNT:")
print(len(factory.improvement_executor.history()))

print()

print("AUDIT HISTORY COUNT:")
print(len(factory.improvement_audit.history()))
