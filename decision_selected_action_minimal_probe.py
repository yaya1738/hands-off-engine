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

result = factory.decision.select_action(options)

selected = result.get("selected")

print("SELECTED ACTION")
print("=" * 30)

print("TYPE:", type(selected).__name__)

if isinstance(selected, dict):
    print("KEYS:", list(selected.keys()))

print("DONE")
