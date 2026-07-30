from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

targets = [
    "improvement_orchestrator",
    "improvement_pipeline",
    "improvement_planner",
    "improvement_prioritizer",
    "goal_optimizer",
    "strategy_manager",
]

report = {}

for t in targets:
    obj = getattr(r, t, None)

    report[t] = {
        "exists": obj is not None,
        "type": type(obj).__name__ if obj else None,
    }

print({
    "status": "ANALYZED",
    "components": report,
    "next_action": "MAP_PRIORITY_OWNER"
})
