from ai.factory.runtime import FactoryRuntime

result = {
    "goal": "IMPROVEMENT_CHECKPOINT_INTEGRATION",
    "checks": {},
    "errors": [],
}

try:
    r = FactoryRuntime()

    result["checks"]["runtime_loaded"] = True

    result["checks"]["improvement_cycle"] = hasattr(
        r,
        "run_improvement_cycle",
    )

    result["checks"]["checkpoint_cycle"] = hasattr(
        r,
        "run_checkpoint_cycle",
    )

    result["checks"]["audit"] = hasattr(
        r,
        "improvement_audit",
    )

    result["checks"]["improvement_orchestrator"] = hasattr(
        r,
        "improvement_orchestrator",
    )

    if all(result["checks"].values()):
        result["status"] = "PASS"
        result["next_action"] = "WIRE_LIFECYCLE"
    else:
        result["status"] = "BLOCKED"
        result["next_action"] = "REPAIR_MISSING_LINK"

except Exception as e:
    result["status"] = "ERROR"
    result["errors"].append(str(e))
    result["next_action"] = "RECOVERY"

print(result)
