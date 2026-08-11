from ai.factory.runtime import FactoryRuntime


def test_failure_route_registry_closure():

    runtime = FactoryRuntime()

    failure = {
        "status": "FAILED",
        "component": "repair_loop",
        "error": "closure_test",
    }

    entry = runtime.failure_registry.record_failure(
        failure
    )

    fingerprint = entry["fingerprint"]

    runtime.create_factory_routine(
        "autonomous_repair_cycle",
        "repair failures",
        [
            "detect",
            "repair",
            "learn",
        ],
    )

    result = runtime.route_autonomous_failure_repair(
        failure
    )

    assert result["capability_execution"] is not None

    capability_execution = result["capability_execution"]

    assert capability_execution["status"] == (
        "PENDING_APPROVAL"
    )

    approval_request = capability_execution[
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

    execution_result = runtime.improvement_executor.execute(
        approved_improvement,
        action,
    )

    assert execution_result["status"] == "EXECUTED"

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
