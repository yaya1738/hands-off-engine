from ai.factory.runtime import FactoryRuntime


def evaluate_checkpoint_flow():
    report = {
        "checks": {},
        "errors": [],
        "decision_state": None,
        "execution": None,
    }

    try:
        r = FactoryRuntime()

        decision = r.checkpoint_manager.evaluate()

        report["checks"]["manager_available"] = isinstance(
            decision,
            dict,
        )

        state = decision.get("state")
        report["decision_state"] = state

        if state == "READY_TO_COMMIT":
            execution = r.checkpoint_executor.execute(
                decision
            )

            report["execution"] = execution

            report["checks"]["executor_success"] = (
                execution.get("status")
                == "CHECKPOINT_CREATED"
            )

            report["checks"]["audit_available"] = hasattr(
                r,
                "improvement_audit",
            )

        elif state == "REVIEW_REQUIRED":
            report["checks"]["safe_stop"] = True

        elif state == "BLOCKED":
            report["checks"]["blocked_correctly"] = True

        else:
            report["checks"]["known_state"] = False

    except Exception as e:
        report["errors"].append(str(e))

    if report["errors"]:
        return {
            "state": "ERROR",
            "action": "RECOVERY_REQUIRED",
            "report": report,
        }

    if all(report["checks"].values()):
        return {
            "state": "COMPLETE",
            "action": "CONTINUE_INTEGRATION",
            "report": report,
        }

    return {
        "state": "FAILED",
        "action": "REPAIR_CHECKPOINT_FLOW",
        "report": report,
    }


print(evaluate_checkpoint_flow())
