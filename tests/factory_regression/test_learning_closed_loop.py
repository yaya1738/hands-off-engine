from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

r.learning_loop.record_outcome({
    "action": {
        "type": "autonomous_failure_recovery",
        "failure": {
            "error": "CLOSED_LOOP_TEST_FAILURE"
        }
    }
})

r.run_improvement_cycle({
    "success": True,
    "steps_completed": []
})

print({
    "learning": r.learning_improvement_adapter.history(),
    "planner_history": r.improvement_planner.history(),
    "audit_count": len(r.improvement_audit.history()),
})
