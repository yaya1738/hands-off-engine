from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

payload = {
    "decision": {}
}

print("ADAPTIVE PAYLOAD TEST")
print("=" * 35)

try:
    result = factory.adaptive_decision.decide(payload)

    print("RESULT:", result)

except Exception as e:
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR:", str(e))

print("DONE")
