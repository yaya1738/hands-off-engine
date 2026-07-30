from pathlib import Path

runtime = Path("ai/factory/runtime.py")

result = {
    "status": None,
    "checks": {},
    "findings": [],
    "next_action": None,
}

try:
    text = runtime.read_text()

    has_method = "def run_checkpoint_cycle" in text
    has_review_branch = (
        'state == "REVIEW_REQUIRED"' in text
    )
    has_safe_stop = (
        '"action": "SAFE_STOP"' in text
    )

    result["checks"] = {
        "run_checkpoint_cycle_exists": has_method,
        "review_branch_exists": has_review_branch,
        "safe_stop_action_exists": has_safe_stop,
    }

    if not has_method:
        result["status"] = "FAIL"
        result["findings"].append(
            "checkpoint_cycle_missing"
        )
        result["next_action"] = "ADD_RUNTIME_ENTRYPOINT"

    elif not has_review_branch:
        result["status"] = "FAIL"
        result["findings"].append(
            "review_state_not_handled"
        )
        result["next_action"] = "ADD_SAFE_STOP_BRANCH"

    elif not has_safe_stop:
        result["status"] = "FAIL"
        result["findings"].append(
            "safe_stop_action_missing"
        )
        result["next_action"] = "PATCH_RUNTIME_RESPONSE"

    else:
        result["status"] = "PASS"
        result["findings"].append(
            "runtime_contains_safe_stop_logic"
        )
        result["next_action"] = "TRACE_EXECUTION_PATH"

except Exception as e:
    result["status"] = "ERROR"
    result["findings"].append(str(e))
    result["next_action"] = "RECOVERY"

print(result)
