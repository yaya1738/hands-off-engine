from ai.factory.runtime import FactoryRuntime

try:
    r = FactoryRuntime()

    output = r.run_checkpoint_cycle()

    if output.get("status") == "COMPLETE":
        print({
            "status": "PASS",
            "action": "CHECKPOINT_LIFECYCLE_ACTIVE",
            "output": output,
        })
    else:
        print({
            "status": "BLOCKED",
            "action": "REVIEW_REQUIRED",
            "output": output,
        })

except Exception as e:
    print({
        "status": "ERROR",
        "action": "RECOVERY_REQUIRED",
        "error": str(e),
    })
