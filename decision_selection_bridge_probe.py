from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

options = [
    {
        "action": "test_action",
        "score": 1,
        "context": {},
        "validation": [],
        "rollback": [],
    }
]

decision = factory.decision.evaluate_options(options)

print("DECISION SELECTION BRIDGE")
print("=" * 35)

print("EVALUATED KEYS:", list(decision.keys()))

try:
    selected = factory.decision.select_action(options)
    print("SELECT TYPE:", type(selected).__name__)
    if isinstance(selected, dict):
        print("SELECT KEYS:", list(selected.keys()))
except Exception as e:
    print("ERROR:", type(e).__name__)
    print("DETAIL:", str(e))

print("DONE")
