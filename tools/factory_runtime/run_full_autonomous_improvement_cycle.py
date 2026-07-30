from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

cycle = r.run_autonomous_improvement()

execution = r.execute_autonomous_improvements(
    cycle
)

print({
    "status": "FULL_AUTONOMOUS_IMPROVEMENT_CYCLE",
    "cycle": cycle,
    "execution": execution
})
