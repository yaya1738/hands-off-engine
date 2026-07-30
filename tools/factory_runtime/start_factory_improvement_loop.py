from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.run_improvement_cycle({
    "success": True,
    "source": "autonomous_cycle_start",
    "trigger": "runtime_request"
})

print({
    "status": "STARTED",
    "result": result
})
