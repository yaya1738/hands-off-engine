from ai.factory.runtime import FactoryRuntime

def decide(checks):
    missing = [
        name for name, value in checks.items()
        if not value
    ]

    if not missing:
        return {
            "decision": "CONNECT_VALIDATION_GATE",
            "reason": "ALL_COMPONENTS_EXIST"
        }

    if "executor" in missing:
        return {
            "decision": "CREATE_VALIDATION_EXECUTOR",
            "reason": "NO_EXECUTION_AUTHORITY"
        }

    if "audit" in missing:
        return {
            "decision": "CREATE_VALIDATION_AUDIT_PATH",
            "reason": "NO_PROVENANCE"
        }

    if "learning" in missing:
        return {
            "decision": "CONNECT_LEARNING_FEEDBACK",
            "reason": "NO_IMPROVEMENT_MEMORY"
        }

    return {
        "decision": "DISCOVER_MISSING_CAPABILITY",
        "missing": missing
    }


try:
    r = FactoryRuntime()

    checks = {
        "audit": hasattr(r, "improvement_audit"),
        "executor": hasattr(r, "improvement_executor"),
        "learning": hasattr(r, "learning"),
        "orchestrator": hasattr(r, "improvement_orchestrator"),
    }

    print({
        "status": "ANALYZED",
        "checks": checks,
        "next_action": decide(checks)
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVER_RUNTIME_VALIDATION"
    })
