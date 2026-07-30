from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

print({
    "executor_history": r.improvement_executor.history(),
    "improvement_audit": r.improvement_audit.history(),
    "orchestrator_history": r.improvement_orchestrator.history(),
})
