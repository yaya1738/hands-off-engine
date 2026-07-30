from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.improvement_orchestrator.run_cycle()

print({
    "status": "FACTORY_SELF_IMPROVEMENT_CYCLE_COMPLETE",
    "result": result
})
