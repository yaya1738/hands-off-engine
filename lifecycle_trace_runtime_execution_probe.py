from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "runtime trace integration test",
    "factory"
)

trace = factory.lifecycle_trace.trace()

print("RUNTIME TRACE INTEGRATION")
print("=" * 35)

print("STATUS:", trace["lifecycle_status"])
print("TASK:", trace["task_id"])
print("ARTIFACT:", trace["artifact_id"])
print("IMPROVEMENT:", trace["improvement_id"])
print("AUDIT:", trace["audit_present"])

print("DONE")
