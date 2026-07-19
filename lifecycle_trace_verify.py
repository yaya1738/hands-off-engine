from ai.factory.runtime import FactoryRuntime
from ai.factory.lifecycle_trace import FactoryLifecycleTrace

factory = FactoryRuntime()

factory.submit_development_request(
    "trace adapter verification",
    "factory"
)

trace = FactoryLifecycleTrace(factory)

result = trace.trace()

print("LIFECYCLE TRACE VERIFY")
print("=" * 35)

for key, value in result.items():
    if isinstance(value, dict):
        print(key + ":", "PRESENT")
    else:
        print(key + ":", value)

print("DONE")
