from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.run_autonomous_improvement()

print({
    "status": result.get("status"),
    "success": result.get("success"),
    "failure": result.get("failure"),
    "execution_count": result.get("execution", {}).get("count"),
    "audit_entries": len(r.improvement_audit.history()),
    "checkpoint_entries": len(r.checkpoint_executor.history()),
})
