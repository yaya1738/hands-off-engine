from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.run_autonomous_improvement()

execution = result.get("execution", {})

completed = [
    item for item in execution.get("executed", [])
    if item.get("status") == "EXECUTED"
]

print({
    "autonomous_cycle": bool(result.get("cycle")),
    "actions_executed": len(completed),
    "actions_completed": len(completed) == execution.get("count", 0),
    "audit_entries": len(r.improvement_audit.history()),
    "executor_entries": len(r.improvement_executor.history()),
    "orchestrator_entries": len(r.improvement_orchestrator.history()),
    "checkpoint_entries": len(r.checkpoint_executor.history()),
})
