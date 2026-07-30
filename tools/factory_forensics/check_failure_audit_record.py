from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

def fail_cycle(*args, **kwargs):
    raise Exception("TEST_AUTONOMOUS_FAILURE")

r.improvement_orchestrator.run_cycle = fail_cycle

r.run_autonomous_improvement()

print({
    "audit_count": len(r.improvement_audit.history()),
    "latest": r.improvement_audit.history()[-1],
})
