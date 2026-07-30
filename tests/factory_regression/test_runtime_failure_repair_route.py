from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

def fail_cycle(*args, **kwargs):
    raise Exception("TEST_AUTONOMOUS_FAILURE")

r.improvement_orchestrator.run_cycle = fail_cycle

result = r.run_autonomous_improvement()

print({
    "status": result.get("status"),
    "has_repair_route": "repair_route" in result,
    "repair_route_status": result.get("repair_route", {}).get("status"),
})
