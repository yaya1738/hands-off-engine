from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.run_autonomous_improvement()

print({
    "result": result,
    "checkpoint_manager": r.checkpoint_manager.__dict__,
    "audit": r.improvement_audit.history(),
})
