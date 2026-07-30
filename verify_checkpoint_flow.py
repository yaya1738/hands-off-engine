from ai.factory.runtime import FactoryRuntime

result = {
    "status": "FAIL",
    "goal": "CHECKPOINT_SIGNAL_FLOW",
    "checks": {},
    "errors": [],
}

try:
    r = FactoryRuntime()

    decision = r.checkpoint_manager.evaluate()

    result["checks"]["manager_produced_decision"] = isinstance(
        decision,
        dict,
    )

    result["checks"]["decision_has_state"] = (
        "state" in decision
    )

    if decision.get("state") == "READY_TO_COMMIT":
        execution = r.checkpoint_executor.execute(
            decision
        )

        result["checks"]["executor_received_decision"] = (
            isinstance(execution, dict)
        )

        result["checks"]["executor_completed"] = (
            execution.get("status")
            == "CHECKPOINT_CREATED"
        )

    else:
        execution = {
            "status": "NOT_READY"
        }

    result["checks"]["audit_available"] = hasattr(
        r,
        "improvement_audit",
    )

    passed = all(
        result["checks"].values()
    )

    result["status"] = (
        "PASS"
        if passed
        else "FAIL"
    )

    result["next_action"] = (
        "CONTINUE_INTEGRATION"
        if passed
        else "REPAIR_SIGNAL_FLOW"
    )

except Exception as e:
    result["status"] = "ERROR"
    result["errors"].append(str(e))
    result["next_action"] = "RECOVERY_REQUIRED"

print(result)
