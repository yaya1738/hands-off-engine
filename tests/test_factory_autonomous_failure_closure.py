from ai.factory.runtime import FactoryRuntime


def test_factory_autonomous_failure_closure():

    runtime = FactoryRuntime()

    failure = {
        "status": "FAILED",
        "component": "factory_cycle_test",
        "error": "closure_test",
    }

    entry = runtime.failure_registry.record_failure(
        failure
    )

    fingerprint = entry["fingerprint"]

    improvement = {
        "name": "closure_test",
        "priority": 1,
        "status": "APPROVED",
        "failure_fingerprint": fingerprint,
    }

    runtime.improvement_queue.enqueue(
        improvement
    )

    queued = runtime.improvement_queue.history()

    pending_result = runtime.execute_autonomous_improvements(
        {
            "queue": queued
        }
    )

    assert pending_result["executed"]
    assert pending_result["executed"][0]["status"] == (
        "PENDING_APPROVAL"
    )

    approval_request = pending_result["executed"][0][
        "approval_request"
    ]

    approval_result = runtime.improvement_approval.approve(
        approval_request
    )

    assert approval_result["status"] == "APPROVED"

    approved_improvement = approval_result["improvement"]

    action = runtime.improvement_action_resolver.resolve(
        {
            "action": approved_improvement.get(
                "name",
                approved_improvement.get("action"),
            ),
            **approved_improvement,
        }
    )

    result = runtime.improvement_executor.execute(
        approved_improvement,
        action,
    )

    assert result["status"] == "EXECUTED"

    runtime.failure_registry.resolve(
        fingerprint,
        {
            "status": "EXECUTED",
            "source": "approval_regression_contract",
        },
    )

    final = runtime.failure_registry.find(
        fingerprint
    )

    assert final["status"] == "RESOLVED"
