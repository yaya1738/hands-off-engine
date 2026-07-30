from ai.factory.runtime import FactoryRuntime


EXPECTED_BEHAVIORS = {
    "READY_TO_COMMIT": "CHECKPOINT_CREATED",
    "REVIEW_REQUIRED": "SAFE_STOP",
    "BLOCKED": "NO_EXECUTION",
}


def evaluate():
    try:
        r = FactoryRuntime()

        result = r.run_checkpoint_cycle()

        decision = result.get("decision", {})
        state = decision.get("state")

        expected_action = EXPECTED_BEHAVIORS.get(state)

        actual_action = (
            result.get("action")
            or result.get("execution", {}).get("status")
        )

        matched = (
            expected_action is not None
            and (
                actual_action == expected_action
                or state == "REVIEW_REQUIRED"
                and actual_action == "SAFE_STOP"
            )
        )

        return {
            "status": "PASS" if matched else "REVIEW",
            "goal": "FACTORY_CHECKPOINT_BEHAVIOR",
            "decision_state": state,
            "expected_behavior": expected_action,
            "actual_behavior": actual_action,
            "next_action": (
                "CONTINUE"
                if matched
                else "ADJUST_FLOW"
            ),
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "goal": "FACTORY_CHECKPOINT_BEHAVIOR",
            "error": str(e),
            "next_action": "RECOVERY",
        }


print(evaluate())
