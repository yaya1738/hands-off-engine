from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

improvement = {
    "id": 1,
    "status": "APPROVED",
    "objective": "router bridge test",
}

def test_action():
    return "action_completed"

result = factory.process_approved_improvement(
    improvement,
    test_action,
)

print("RESULT STATUS:")
print(result.get("status"))

print("\nEXECUTOR HISTORY:")
print(len(factory.improvement_executor.history()))

print("\nAUDIT HISTORY:")
print(len(factory.improvement_audit.history()))

print("\nLAST AUDIT TYPE:")
print(
    factory.improvement_audit.history()[-1]["action"].get("type")
)
