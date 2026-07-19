from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("RUNTIME DECISION ADAPTER")
print("=" * 35)

print("DECISION:", type(factory.decision).__name__)

print(
    "ADAPTER:",
    type(factory.decision_option_adapter).__name__
)

print("DONE")
