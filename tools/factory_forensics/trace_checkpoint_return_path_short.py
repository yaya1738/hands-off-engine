from ai.factory.runtime import FactoryRuntime
import inspect

try:
    source = inspect.getsource(
        FactoryRuntime.run_checkpoint_cycle
    )

    r = FactoryRuntime()
    output = r.run_checkpoint_cycle()

    decision = output.get("decision", {})

    checks = {
        "method_loaded": True,
        "review_in_method": "REVIEW_REQUIRED" in source,
        "safe_stop_in_method": "SAFE_STOP" in source,
        "decision_state": decision.get("state"),
        "returned_action": output.get("action"),
    }

    if (
        checks["decision_state"] == "REVIEW_REQUIRED"
        and checks["returned_action"] != "SAFE_STOP"
        and checks["safe_stop_in_method"]
    ):
        result = {
            "status": "MISMATCH",
            "cause": "RETURN_PATH_BYPASS",
            "next_action": "TRACE_BRANCH",
        }

    elif not checks["safe_stop_in_method"]:
        result = {
            "status": "MISSING",
            "cause": "SAFE_STOP_NOT_IMPLEMENTED",
            "next_action": "PATCH_METHOD",
        }

    else:
        result = {
            "status": "PASS",
            "cause": "EXPECTED_BEHAVIOR",
            "next_action": "CONTINUE",
        }

    result["checks"] = checks
    print(result)

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVERY",
    })
