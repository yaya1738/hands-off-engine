from ai.factory.runtime import FactoryRuntime

report = {
    "status": None,
    "checks": {},
    "next_action": None,
}

try:
    r = FactoryRuntime()

    before_learning = len(r.learning.experiences)

    checkpoint = r.run_checkpoint_cycle()

    after_learning = len(r.learning.experiences)

    report["checks"]["runtime_loaded"] = True
    report["checks"]["checkpoint_result"] = isinstance(checkpoint, dict)
    report["checks"]["checkpoint_action"] = checkpoint.get("action")
    report["checks"]["learning_updated"] = after_learning > before_learning
    report["checks"]["audit_available"] = hasattr(
        r,
        "improvement_audit"
    )

    if all([
        report["checks"]["runtime_loaded"],
        report["checks"]["checkpoint_result"],
        report["checks"]["learning_updated"],
        report["checks"]["audit_available"],
    ]):
        report["status"] = "PASS"
        report["next_action"] = "CONTINUE_INTEGRATION"
    else:
        report["status"] = "FAIL"
        report["next_action"] = "TRACE_FAILED_LINK"

    report["details"] = {
        "learning_before": before_learning,
        "learning_after": after_learning,
    }

except Exception as e:
    report["status"] = "ERROR"
    report["next_action"] = "RECOVERY"
    report["error"] = str(e)

print(report)
