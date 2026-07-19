from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("EXECUTION OBSERVABILITY")
print("=" * 35)

print("HAS OBSERVABILITY:", hasattr(factory, "observability"))

print("EXECUTE METHODS:")
for name in [
    "execute",
    "autonomous_execute",
    "execute_approved_improvement",
]:
    if hasattr(factory, name):
        print(name, "YES")

print("DONE")
