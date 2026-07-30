
from ai.factory.runtime import FactoryRuntime


def test_review_required_safe_stop():
    runtime = FactoryRuntime()

    output = runtime.run_checkpoint_cycle()

    decision_state = (
        output.get("decision", {})
        .get("state")
    )

    if decision_state == "REVIEW_REQUIRED":
        assert output.get("action") == "SAFE_STOP"


def test_checkpoint_response_has_action():
    runtime = FactoryRuntime()

    output = runtime.run_checkpoint_cycle()

    assert (
        "action" in output
        or output.get("status") == "ERROR"
    )


def test_ready_to_commit_executes_checkpoint():
    runtime = FactoryRuntime()

    output = runtime.run_checkpoint_cycle()

    decision_state = (
        output.get("decision", {})
        .get("state")
    )

    if decision_state == "READY_TO_COMMIT":
        assert (
            output.get("action")
            == "CHECKPOINT_EXECUTED"
        )


def test_blocked_prevents_execution():
    runtime = FactoryRuntime()

    output = runtime.run_checkpoint_cycle()

    decision_state = (
        output.get("decision", {})
        .get("state")
    )

    if decision_state == "BLOCKED":
        assert (
            output.get("action")
            == "NO_EXECUTION"
        )
