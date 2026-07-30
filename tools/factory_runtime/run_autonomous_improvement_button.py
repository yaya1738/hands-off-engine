from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.run_autonomous_improvement()

print({
    "status": "AUTONOMOUS_IMPROVEMENT_RUN",
    "result": result
})
