from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("GAP SOURCE COMPONENTS")
print("=" * 35)

for name in [
    "improvement_assessment",
    "assessment",
    "self_assessment",
    "diagnostics",
    "diagnostic_intelligence",
    "recommendations",
]:
    if hasattr(factory, name):
        print(name, "=>", type(getattr(factory, name)).__name__)

print("DONE")
