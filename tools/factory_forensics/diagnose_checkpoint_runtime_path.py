from pathlib import Path
import re

p = Path("ai/factory/runtime.py")

result = {
    "status": None,
    "diagnosis": [],
    "checks": {},
    "next_action": None,
}

try:
    text = p.read_text()

    method_match = re.search(
        r"def run_checkpoint_cycle\(.*?(?=\n    def |\Z)",
        text,
        re.S,
    )

    result["checks"]["method_exists"] = (
        method_match is not None
    )

    if method_match:
        method = method_match.group()

        result["checks"]["review_branch_exists"] = (
            "REVIEW_REQUIRED" in method
        )

        result["checks"]["safe_stop_action_exists"] = (
            "SAFE_STOP" in method
        )

        result["checks"]["decision_returned"] = (
            "decision" in method
        )

        result["checks"]["method_returns_result"] = (
            "return" in method
        )

    else:
        result["checks"]["review_branch_exists"] = False
        result["checks"]["safe_stop_action_exists"] = False
        result["checks"]["decision_returned"] = False
        result["checks"]["method_returns_result"] = False


    if not result["checks"]["method_exists"]:
        result["diagnosis"].append(
            "METHOD_MISSING"
        )
        result["next_action"] = (
            "ADD_RUN_CHECKPOINT_CYCLE"
        )

    elif not result["checks"]["review_branch_exists"]:
        result["diagnosis"].append(
            "REVIEW_BRANCH_MISSING"
        )
        result["next_action"] = (
            "ADD_REVIEW_HANDLING"
        )

    elif not result["checks"]["safe_stop_action_exists"]:
        result["diagnosis"].append(
            "SAFE_STOP_ACTION_MISSING"
        )
        result["next_action"] = (
            "PATCH_SAFE_STOP_RESPONSE"
        )

    else:
        result["diagnosis"].append(
            "CODE_EXISTS_TRACE_RUNTIME_USAGE"
        )
        result["next_action"] = (
            "TRACE_CALL_PATH"
        )


    result["status"] = "ANALYZED"

except Exception as e:
    result["status"] = "ERROR"
    result["diagnosis"].append(str(e))
    result["next_action"] = "RECOVERY"


print(result)
