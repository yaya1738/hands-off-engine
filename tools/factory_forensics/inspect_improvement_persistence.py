from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.run_autonomous_improvement()

print("RUN_RESULT")
print(result)

print("\nSAME_RUNTIME_STATE")
print({
    "executor_history": r.improvement_executor.history(),
    "audit": r.improvement_audit.history(),
    "orchestrator": r.improvement_orchestrator.history(),
})
