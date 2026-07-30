from pathlib import Path

result = {
    "status": None,
    "scenario": None,
    "next_action": None,
    "details": {}
}

try:
    from ai.factory.runtime import FactoryRuntime

    result["details"]["factory_import"] = True

    runtime = FactoryRuntime()

    if not hasattr(runtime, "run_checkpoint_cycle"):
        result["status"] = "BLOCKED"
        result["scenario"] = "CHECKPOINT_CAPABILITY_MISSING"
        result["next_action"] = "REPAIR_FACTORY_LINK"

    else:
        checkpoint = runtime.run_checkpoint_cycle()

        if not isinstance(checkpoint, dict):
            result["status"] = "FAIL"
            result["scenario"] = "CHECKPOINT_BAD_OUTPUT"
            result["next_action"] = "TRACE_CHECKPOINT_RETURN"

        elif "action" not in checkpoint:
            result["status"] = "FAIL"
            result["scenario"] = "CHECKPOINT_ACTION_MISSING"
            result["next_action"] = "ADD_ACTION_MAPPING"

        elif hasattr(runtime, "learning") and hasattr(runtime, "recommendation_feedback"):
            result["status"] = "PASS"
            result["scenario"] = "FACTORY_LINK_READY"
            result["next_action"] = "TRACE_FEEDBACK_PATH"

        else:
            result["status"] = "REVIEW"
            result["scenario"] = "LEARNING_LINK_MISSING"
            result["next_action"] = "CONNECT_FEEDBACK_LAYER"

        result["details"]["checkpoint"] = checkpoint.get("action")

except ImportError as e:
    result["status"] = "ERROR"
    result["scenario"] = "FACTORY_IMPORT_FAILED"
    result["next_action"] = "RECOVER_IMPORT"
    result["details"]["error"] = str(e)

except Exception as e:
    result["status"] = "ERROR"
    result["scenario"] = "RUNTIME_EXCEPTION"
    result["next_action"] = "TRACE_FAILURE"
    result["details"]["error"] = str(e)

print(result)
