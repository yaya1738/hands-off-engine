from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("RUNTIME DECISION CHECK")
print("=" * 30)

print(
    "HAS DECISION:",
    hasattr(factory, "decision")
)

if hasattr(factory, "decision"):
    print(
        "TYPE:",
        type(factory.decision).__name__
    )

print("DONE")
