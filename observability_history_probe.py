from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

obs = factory.observability

print("OBSERVABILITY HISTORY")
print("=" * 35)

history = obs.history()

print("TYPE:", type(history).__name__)

if isinstance(history, list):
    print("COUNT:", len(history))

print("DONE")
