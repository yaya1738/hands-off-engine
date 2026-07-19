from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("METRIC SOURCES")
print("=" * 30)

for name in [
    "observability",
    "state",
    "diagnostics",
    "diagnostic_intelligence",
    "performance",
    "metrics",
]:
    if hasattr(factory, name):
        print(name, "=>", type(getattr(factory, name)).__name__)

print("DONE")
