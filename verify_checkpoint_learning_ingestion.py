from ai.factory.runtime import FactoryRuntime
import inspect

try:
    r = FactoryRuntime()

    checkpoint = r.run_checkpoint_cycle()

    learning = r.learning

    method = getattr(
        learning,
        "record_experience",
        None
    )

    result = {
        "status": None,
        "checks": {},
        "next_action": None,
    }

    result["checks"]["checkpoint_output"] = (
        isinstance(checkpoint, dict)
    )

    result["checks"]["learning_ingest_exists"] = (
        callable(method)
    )

    if callable(method):
        sig = inspect.signature(method)
        result["checks"]["ingest_accepts_input"] = (
            len(sig.parameters) >= 1
        )

    passed = all(result["checks"].values())

    result["status"] = (
        "PASS" if passed else "FAIL"
    )

    result["next_action"] = (
        "WIRE_CHECKPOINT_TO_LEARNING"
        if passed
        else "REPAIR_INTERFACE"
    )

    print(result)

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVERY",
    })
