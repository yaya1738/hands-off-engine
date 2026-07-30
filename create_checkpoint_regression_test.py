from pathlib import Path

test = Path("tests/test_checkpoint_behavior.py")

content = r'''
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
'''

test.write_text(content)

print("CHECKPOINT_REGRESSION_TEST_CREATED")
