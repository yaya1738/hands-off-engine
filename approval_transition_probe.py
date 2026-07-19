from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

request = factory.improvement_approval.request(
    {
        "objective": "executor bridge verification"
    }
)

print("BEFORE:")
print(request["status"])

approved = factory.improvement_approval.approve(
    request
)

print()
print("AFTER:")
print(approved["status"])

print()
print("HISTORY COUNT:")
print(len(factory.improvement_approval.history()))
