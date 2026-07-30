from ai.factory.runtime import FactoryRuntime

report = {
    "status": None,
    "checks": {},
    "next_action": None,
}

try:
    r = FactoryRuntime()

    report["checks"]["runtime_loaded"] = True

    report["checks"]["learning_available"] = hasattr(
        r,
        "learning"
    )

    report["checks"]["improvement_available"] = hasattr(
        r,
        "improvement_orchestrator"
    )

    report["checks"]["prioritizer_available"] = hasattr(
        r,
        "improvement_prioritizer"
    )

    report["checks"]["strategy_available"] = hasattr(
        r,
        "strategy_manager"
    )

    experience_before = len(
        r.learning.experiences
    )

    r.run_checkpoint_cycle()

    experience_after = len(
        r.learning.experiences
    )

    report["checks"]["experience_created"] = (
        experience_after > experience_before
    )

    report["details"] = {
        "learning_before": experience_before,
        "learning_after": experience_after,
    }

    if all(report["checks"].values()):
        report["status"] = "PASS"
        report["next_action"] = "TRACE_PRIORITY_FLOW"
    else:
        report["status"] = "FAIL"
        report["next_action"] = "CONNECT_MISSING_COMPONENT"

except Exception as e:
    report["status"] = "ERROR"
    report["next_action"] = "RECOVERY"
    report["error"] = str(e)

print(report)
