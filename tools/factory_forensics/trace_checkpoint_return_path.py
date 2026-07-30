from pathlib import Path
from ai.factory.runtime import FactoryRuntime
import inspect

result = {
    "status": None,
    "checks": {},
    "findings": [],
}

try:
    source = inspect.getsource(
        FactoryRuntime.run_checkpoint_cycle
    )

    result["checks"]["method_loaded"] = True
    result["checks"]["contains_safe_stop"] = (
        "SAFE_STOP" in source
    )
    result["checks"]["contains_review"] = (
        "REVIEW_REQUIRED" in source
    )

    r = FactoryRuntime()
    output = r.run_checkpoint_cycle()

    result["checks"]["runtime_called"] = True
    result["runtime_output"] = output

    if (
        result["checks"]["contains_safe_stop"]
        and output.get("action") is None
    ):
        result["findings"].append(
            "CODE_EXISTS_BUT_RETURN_PATH_NOT_USING_IT"
        )
        result["next_action"] = (
            "TRACE_RETURN_BRANCH"
        )

    elif not result["checks"]["contains_safe_stop"]:
        result["findings"].append(
            "SAFE_STOP_NOT_IN_LOADED_METHOD"
        )
        result["next_action"] = (
            "PATCH_METHOD"
        )

    else:
        result["findings"].append(
            "BEHAVIOR_MATCHES"
        )
        result["next_action"] = (
            "CONTINUE"
        )

    result["status"] = "ANALYZED"

except Exception as e:
    result["status"] = "ERROR"
    result["findings"].append(str(e))

print(result)
