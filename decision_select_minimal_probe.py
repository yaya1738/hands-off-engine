from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

options = [
    {
        "action": "test_action",
        "score": 1,
        "context": "test",
        "validation": [],
        "rollback": [],
    }
]

print("DECISION SELECT MINIMAL")
print("=" * 35)

selected = factory.decision.select_action(options)

print("TYPE:", type(selected).__name__)

if isinstance(selected, dict):
    print("KEYS:", list(selected.keys()))

print("DONE")
