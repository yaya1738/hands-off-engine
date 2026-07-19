from ai.factory.runtime import FactoryRuntime
import inspect

factory = FactoryRuntime()

print("ADAPTIVE DECIDE SIGNATURE")
print("=" * 35)

print(
    inspect.signature(factory.adaptive_decision.decide)
)

print("DONE")
