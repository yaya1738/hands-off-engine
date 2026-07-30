from ai.factory.runtime import FactoryRuntime
import py_compile

result = {
    "status": None,
    "checks": {},
    "next_action": None
}

try:
    # Syntax check
    py_compile.compile(
        "ai/factory/runtime.py",
        doraise=True
    )
    result["checks"]["runtime_compile"] = True

    runtime = FactoryRuntime()

    result["checks"]["learning_available"] = hasattr(
        runtime,
        "learning"
    )

    before = len(
        runtime.learning.experiences
    )

    checkpoint = runtime.run_checkpoint_cycle()

    after = len(
        runtime.learning.experiences
    )

    result["checks"]["checkpoint_returns"] = isinstance(
        checkpoint,
        dict
    )

    result["checks"]["checkpoint_action"] = checkpoint.get(
        "action"
    )

    result["checks"]["learning_changed"] = after > before

    if all([
        result["checks"]["runtime_compile"],
        result["checks"]["learning_available"],
        result["checks"]["checkpoint_returns"],
        result["checks"]["learning_changed"],
    ]):
        result["status"] = "PASS"
        result["next_action"] = "CONTINUE_INTEGRATION"
    else:
        result["status"] = "FAIL"
        result["next_action"] = "TRACE_FAILED_CHECK"

    result["details"] = {
        "learning_before": before,
        "learning_after": after,
        "checkpoint_action": checkpoint.get("action")
    }

except Exception as e:
    result["status"] = "ERROR"
    result["next_action"] = "RECOVERY"
    result["error"] = str(e)

print(result)
