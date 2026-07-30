from ai.factory.runtime import FactoryRuntime

EXPECTED = {
    "decision_state": "REVIEW_REQUIRED",
    "action": "SAFE_STOP",
}


def check():
    try:
        r = FactoryRuntime()
        output = r.run_checkpoint_cycle()

        decision_state = (
            output.get("decision", {})
            .get("state")
        )

        action = output.get("action")

        checks = {
            "decision_state": (
                decision_state
                == EXPECTED["decision_state"]
            ),
            "action": (
                action
                == EXPECTED["action"]
            ),
        }

        passed = all(checks.values())

        return {
            "status": (
                "PASS"
                if passed
                else "FAIL"
            ),
            "expected": EXPECTED,
            "actual": {
                "decision_state": decision_state,
                "action": action,
            },
            "checks": checks,
            "next_action": (
                "CONTINUE"
                if passed
                else "FIX_MISMATCH"
            ),
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "next_action": "RECOVERY",
        }


print(check())
