from ai.factory.runtime import FactoryRuntime

try:
    r = FactoryRuntime()

    checks = {}

    checks["runtime_loaded"] = True
    checks["assessment_available"] = hasattr(
        r,
        "improvement_assessment"
    )
    checks["orchestrator_available"] = hasattr(
        r,
        "improvement_orchestrator"
    )
    checks["executor_available"] = hasattr(
        r,
        "improvement_executor"
    )
    checks["audit_available"] = hasattr(
        r,
        "improvement_audit"
    )
    checks["learning_available"] = hasattr(
        r,
        "learning"
    )

    if all(checks.values()):
        next_action = "RUN_IMPROVEMENT_CYCLE_TEST"
    else:
        next_action = "REPAIR_MISSING_COMPONENT"

    print({
        "status": "ANALYZED",
        "checks": checks,
        "next_action": next_action
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVER_RUNTIME"
    })
