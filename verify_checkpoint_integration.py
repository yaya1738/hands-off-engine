from ai.factory.runtime import FactoryRuntime

EXPECTED = {
    "status": "CHECKPOINT_CREATED",
    "state": "COMPLETED",
}

result = {}

try:
    r = FactoryRuntime()

    output = r.checkpoint_executor.execute(
        {
            "state": "READY_TO_COMMIT",
            "action": "CREATE_CHECKPOINT",
        }
    )

    passed = all(
        output.get(k) == v
        for k, v in EXPECTED.items()
    )

    result = {
        "status": "PASS" if passed else "FAIL",
        "action": (
            "CONTINUE_INTEGRATION"
            if passed
            else "REPAIR_CHECKPOINT_EXECUTOR"
        ),
        "output": output,
        "expected": EXPECTED,
    }

except Exception as e:
    result = {
        "status": "ERROR",
        "action": "RECOVERY_REQUIRED",
        "error": str(e),
    }

print(result)
