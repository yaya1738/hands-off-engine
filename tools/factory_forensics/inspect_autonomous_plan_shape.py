from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

cycle = r.improvement_orchestrator.run_cycle({
    "success_rate": 0,
    "average_impact": 0
})

print({
    "plan": cycle.get("plan"),
    "tasks_type": type(cycle.get("plan", {}).get("tasks")).__name__,
    "tasks": cycle.get("plan", {}).get("tasks")
})
