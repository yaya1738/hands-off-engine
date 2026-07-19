from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("RUNTIME OPERATIONS REPORT")
print("=" * 30)

print(factory.get_operations_report())

print("DONE")
