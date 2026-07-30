from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

def fail_cycle(*args, **kwargs):
    raise Exception("TEST_AUTONOMOUS_FAILURE")

r.improvement_orchestrator.run_cycle = fail_cycle

r.run_autonomous_improvement()

print({
    "learning_history_count": len(r.learning_loop.history()),
    "latest_learning": r.learning_loop.history()[-1]
})
