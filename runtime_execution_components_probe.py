from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("RUNTIME EXECUTION COMPONENTS")
print("=" * 35)

for name in [
    "improvement_executor",
    "improvement_audit",
    "improvement_approval",
    "decision_option_adapter",
]:
    obj = getattr(factory, name, None)
    print(name, "=>", type(obj).__name__ if obj else "MISSING")

print("DONE")
