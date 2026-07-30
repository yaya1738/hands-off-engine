from ai.factory.runtime import FactoryRuntime

def next_action(state):
    checks = state.get("checks", {})
    decision = state.get("next_action", {})

    if decision.get("decision") == "CONNECT_VALIDATION_GATE":
        return {
            "action": "WIRE_VALIDATION_INTO_IMPROVEMENT_EXECUTION",
            "reason": "CAPABILITIES_EXIST_BUT_NOT_CONNECTED"
        }

    if decision.get("decision") == "CREATE_VALIDATION_EXECUTOR":
        return {
            "action": "CREATE_VALIDATION_EXECUTION_CAPABILITY",
            "reason": "EXECUTION_LAYER_MISSING"
        }

    if decision.get("decision") == "CREATE_VALIDATION_AUDIT_PATH":
        return {
            "action": "CREATE_VALIDATION_AUDIT_PATH",
            "reason": "PROVENANCE_MISSING"
        }

    if decision.get("decision") == "CONNECT_LEARNING_FEEDBACK":
        return {
            "action": "CONNECT_VALIDATION_TO_LEARNING",
            "reason": "FEEDBACK_LOOP_MISSING"
        }

    if decision.get("decision") == "DISCOVER_MISSING_CAPABILITY":
        return {
            "action": "RUN_CAPABILITY_DISCOVERY",
            "reason": "UNKNOWN_GAP"
        }

    return {
        "action": "VERIFY_EXISTING_IMPROVEMENT_LOOP",
        "reason": "NO_REPAIR_REQUIRED"
    }


try:
    r = FactoryRuntime()

    state = {
        "checks": {
            "audit": hasattr(r, "improvement_audit"),
            "executor": hasattr(r, "improvement_executor"),
            "learning": hasattr(r, "learning"),
            "orchestrator": hasattr(r, "improvement_orchestrator"),
        }
    }

    print({
        "status": "ANALYZED",
        "state": state,
        "next_action": next_action(state)
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVER_RUNTIME"
    })
