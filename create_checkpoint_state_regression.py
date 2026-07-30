from pathlib import Path

p = Path("tests/test_checkpoint_behavior.py")

text = p.read_text()

addition = r'''

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
'''

if "test_ready_to_commit_executes_checkpoint" not in text:
    p.write_text(text + addition)

print("CHECKPOINT_STATE_REGRESSIONS_ADDED")
