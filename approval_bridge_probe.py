from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

result = factory.submit_development_request(
    "approval bridge verification",
    "test"
)

print("RESULT STATUS:")
print(result["task"]["status"])

print()

print("APPROVAL HISTORY COUNT:")
print(len(factory.improvement_approval.history()))

print()

print("EXECUTOR HISTORY COUNT:")
print(len(factory.improvement_executor.history()))

print()

if factory.improvement_approval.history():
    print("APPROVAL STATUS:")
    print(
        factory.improvement_approval.history()[0]["status"]
    )
