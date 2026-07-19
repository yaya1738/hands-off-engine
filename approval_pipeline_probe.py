from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

request = factory.improvement_approval.request(
    {
        "name": "pipeline_test",
        "status": "PENDING",
    }
)

factory.improvement_approval.approve(
    request
)

result = factory.process_approval_pipeline(
    request,
    lambda: "pipeline_execution_success",
)

print("RESULT STATUS:")
print(result.get("status"))

print()

print("EXECUTOR HISTORY:")
print(len(factory.improvement_executor.history()))

print()

print("AUDIT HISTORY:")
print(len(factory.improvement_audit.history()))

print()

print("LAST AUDIT TYPE:")
print(
    factory.improvement_audit.history()[-1]["action"]["type"]
)
