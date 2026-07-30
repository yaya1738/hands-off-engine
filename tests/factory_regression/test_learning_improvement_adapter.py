from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

r.learning_loop.record_outcome({
    "action": {
        "type": "autonomous_failure_recovery",
        "failure": {
            "error": "TEST_REPEATED_FAILURE"
        }
    }
})

print(
    r.learning_improvement_adapter.generate_gap_assessment()
)
