from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

planner = factory.improvement_planner

input_data = {
    "gaps": [
        "decision routing improvement"
    ]
}

print("PLANNER GAP SIGNAL")
print("=" * 35)

result = planner.plan(input_data)

print("TYPE:", type(result).__name__)

if isinstance(result, dict):
    print("TASKS:", len(result.get("tasks", [])))
    print("KEYS:", list(result.keys()))

print("DONE")
