from ai.factory.runtime import FactoryRuntime


EXPECTED = {
    "REVIEW_REQUIRED": "SAFE_STOP",
    "READY_TO_COMMIT": "CHECKPOINT_EXECUTED",
    "BLOCKED": "BLOCKED",
}


def verify():
    try:
        r = FactoryRuntime()

        output = r.run_checkpoint_cycle()

        decision = output.get("decision", {})
        decision_state = decision.get("state")

        expected_action = EXPECTED.get(
            decision_state
        )

        actual_action = output.get(
            "action"
        )

        matched = (
            expected_action is not None
            and actual_action == expected_action
        )

        return {
            "status": (
                "PASS"
                if matched
                else "FAIL"
            ),
            "goal": "CHECKPOINT_STATE_TRANSITION",
            "decision_state": decision_state,
            "expected_action": expected_action,
            "actual_action": actual_action,
            "next_action": (
                "CONTINUE"
                if matched
                else "REPAIR_TRANSITION"
            ),
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "goal": "CHECKPOINT_STATE_TRANSITION",
            "error": str(e),
            "next_action": "RECOVERY",
        }


print(verify())
