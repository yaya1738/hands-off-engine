from ai.factory.runtime import FactoryRuntime

def decide_next_move():
    report = {
        "checks": {},
        "errors": [],
    }

    try:
        r = FactoryRuntime()

        decision = r.checkpoint_manager.evaluate()

        report["checks"]["manager_decision"] = isinstance(
            decision,
            dict,
        )

        if report["checks"]["manager_decision"]:
            report["checks"]["decision_state"] = (
                "state" in decision
            )

        if decision.get("state") == "READY_TO_COMMIT":
            execution = r.checkpoint_executor.execute(
                decision
            )

            report["checks"]["executor"] = (
                execution.get("status")
                == "CHECKPOINT_CREATED"
            )

        else:
            execution = {
                "status": "WAITING"
            }

        report["checks"]["audit"] = hasattr(
            r,
            "improvement_audit",
        )

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
        "state": "BLOCKED",
        "action": "REPAIR_FAILED_COMPONENTS",
        "report": report,
    }


print(decide_next_move())
