from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("ADAPTIVE DECIDE INPUT")
print("=" * 35)

try:
    result = factory.adaptive_decision.decide({})

    print("RESULT TYPE:", type(result).__name__)

    if isinstance(result, dict):
        print("KEYS:", list(result.keys()))

except Exception as e:
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR:", str(e))

print("DONE")
